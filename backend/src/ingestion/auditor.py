import os
import json
import shutil
import asyncio
import csv
from collections import Counter
from pypdf import PdfReader
from lm_broker import LMBroker

# --- 1. CONFIGURATION ---
AUDIT_CONFIG = {
    "provider": "runpod",
    "pod_id": "ia08h1alk1knf7",
    "folder": "silver_no-intent_2024-01-01",  # Target folder from search_and_fetch module 
    "n_votes": 5,               # How many times to query the LLM per PDF for the majority vote trials
    "batch_size": 5,            # How many requests sent to broker in one batch call; infrastructure
    "temperature": 0.7,         # Variation in LLM, SLM responses, 0...1; must be > 0 for votes to diverge; 0 = identical responses every time, 1 = probably meaningless noise
    "concurrency": 2,           # Max PDFs audited simultaneously, pipeline level
    "pages_to_scan": 10,         # How many pages to read from each PDF, to get some coverage of the document, not only the first page 
    "chars_per_page": 200,     # Max characters extracted per page; can not be large
    "char_limit": 4000,         # Hard cap on total characters sent to LLM for safety net; subject to trialing
}

# --- 2. THE AUDIT RUBRIC ---
SYSTEM_PROMPT = "You are a Senior Equity Research Auditor."

USER_PROMPT_TEMPLATE = """
Audit this document snippet. Is it professional institutional investment research?
Criteria: Price targets, supply/demand data, bank disclosures, or deep sector analysis.

Definition of Scores:
5: Institutional (JPM, GS, etc.) with price targets/NAV.
4: High-quality macro/industry reports.
3: Investor decks/factsheets (Promotional but useful).
2: Retail news/blog posts.
1: Spam, broken text, or non-financial.

RETURN JSON ONLY:
{{"is_report": bool, "score": 1-5, "reasoning": "str", "type": "str"}}
"""


class Auditor:
    def __init__(self, raw_folder_name):
        self.raw_dir = os.path.join("data", "raw", raw_folder_name)
        self.proc_dir = os.path.join("data", "processed", raw_folder_name)

        # Setup output structure
        self.final_dir = os.path.join(self.proc_dir, "final")
        self.blocked_dir = os.path.join(self.proc_dir, "blocked")
        os.makedirs(self.final_dir, exist_ok=True)
        os.makedirs(self.blocked_dir, exist_ok=True)

        self.broker = LLMBroker(
            provider=AUDIT_CONFIG["provider"],
            config={"pod_id": AUDIT_CONFIG["pod_id"]}
        )
        self.log_file = os.path.join(self.proc_dir, "audit_trail.csv")

    # --- LOCAL TRIAGE (fast pre-filter before any LLM calls) ---
    def local_triage(self, filename):
        """
        Lightweight pre-filter. Returns True if the file passes basic checks
        and should proceed to SLM or LLM audit. Returns False to block immediately.
        Extend this method with real heuristics as needed (file size, name
        patterns, known-bad signatures, etc.).
        """
        filepath = os.path.join(self.raw_dir, filename)

        # Example checks (add more as your pipeline matures):
        if not os.path.exists(filepath):
            print(f"      [Triage] BLOCKED — file not found: {filename}")
            return False

        if os.path.getsize(filepath) < 1024:   # Suspiciously tiny PDF (<1KB)
            print(f"      [Triage] BLOCKED — file too small: {filename}")
            return False

        # Placeholder for future heuristics (e.g. regex on filename, checksum, etc.)
        return True

    # --- PDF TEXT EXTRACTION ---
    def get_pdf_text(self, filename):
        """
        Extracts text from the first `pages_to_scan` pages,
        capping each page at `chars_per_page` for balanced coverage,
        then applies a hard `char_limit` on the total.
        """
        try:
            reader = PdfReader(os.path.join(self.raw_dir, filename))
            pages = reader.pages[:AUDIT_CONFIG["pages_to_scan"]]

            chunks = []
            for page in pages:
                page_text = page.extract_text() or ""
                chunks.append(page_text[:AUDIT_CONFIG["chars_per_page"]])

            combined = "\n".join(chunks)
            return combined[:AUDIT_CONFIG["char_limit"]]

        except Exception as e:
            return f"Error: {e}"

    # --- CORE AUDIT LOGIC (runs per file, respects semaphore) ---
    async def process_file(self, file_meta, semaphore):
        async with semaphore:
            report_id = file_meta["report_id"]
            filename = f"{report_id}.pdf"
            print(f"   [Audit Start] {report_id}...")

            # 1. Local Triage — fast, cheap pre-filter
            if not self.local_triage(filename):
                self.log_result(report_id, 0, "blocked", "Local Triage Failed")
                return

            # 2. Text Extraction
            snippet = self.get_pdf_text(filename)
            if snippet.startswith("Error:"):
                self.log_result(report_id, 0, "blocked", f"Read Error: {snippet}")
                return

            # 3. Expert Audit — majority voting across n_votes parallel LLM calls
            prompt = USER_PROMPT_TEMPLATE + f"\n\nTEXT:\n{snippet}"
            tasks = [prompt] * AUDIT_CONFIG["n_votes"]
            raw_votes = await self.broker.call_batch(
                tasks,
                system=SYSTEM_PROMPT,
                n_votes=AUDIT_CONFIG["n_votes"],
                batch_size=AUDIT_CONFIG["batch_size"],
                temperature=AUDIT_CONFIG["temperature"]
            )

            # 4. Parse votes
            parsed_votes = []
            for v in raw_votes:
                try:
                    clean = v.replace("```json", "").replace("```", "").strip()
                    parsed_votes.append(json.loads(clean))
                except Exception:
                    continue   # Silently drop malformed responses

            if not parsed_votes:
                self.log_result(report_id, 0, "blocked", "JSON Parse Failure — all votes malformed")
                return

            # 5. Majority vote on score
            scores = [v.get("score", 1) for v in parsed_votes]
            final_score = Counter(scores).most_common(1)[0][0]
            status = "final" if final_score >= 3 else "blocked"

            # Pick reasoning from a representative matching vote
            rep = next(
                (v for v in parsed_votes if v.get("score") == final_score),
                parsed_votes[0]
            )

            # 6. Move file and log
            dest_dir = self.final_dir if status == "final" else self.blocked_dir
            shutil.copy(os.path.join(self.raw_dir, filename), os.path.join(dest_dir, filename))
            self.log_result(report_id, final_score, status, rep.get("reasoning", "n/a"))

    # --- CSV LOGGING ---
    def log_result(self, report_id, score, status, reason):
        write_header = not os.path.exists(self.log_file)
        with open(self.log_file, "a", newline="") as f:
            writer = csv.writer(f)
            if write_header:
                writer.writerow(["report_id", "score", "status", "reasoning"])
            writer.writerow([report_id, score, status, reason])
        print(f"      -> {report_id}: {status.upper()} (Score: {score})")

    # --- ENTRY POINT ---
    async def run(self):
        manifest_path = os.path.join(self.raw_dir, "manifest.json")
        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        sem = asyncio.Semaphore(AUDIT_CONFIG["concurrency"])
        tasks = [
            self.process_file(m, sem)
            for m in manifest
            if m.get("status") == "success"
        ]
        await asyncio.gather(*tasks)


# --- MAIN ---
if __name__ == "__main__":
    folder = AUDIT_CONFIG["folder"]
    auditor = Auditor(folder)
    asyncio.run(auditor.run())
