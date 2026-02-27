import os
import re
import json
import time
import requests
import uuid
from datetime import datetime

# --- 1. CONFIGURATION HUB ---
SERPER_API_KEY = "f16311a42a45b755ee3e08ddfaad24ac460eb0ff"

SEARCH_PARAMS = {
    "subjects": ["palladium", "lithium", "copper"], # Can be a list: ["silver", "gold", "mining"]
    "intent": "outlook",           # Leave as "" for broad search
    "date_after": "2025-01-01",
    "num_results": 20,
    "bank_block": [
        "jpmorgan.com", "goldmansachs.com", "morganstanley.com", 
        "ubs.com", "hsbc.com", "silverinstitute.org"
    ],
    "title_block": ["research", "outlook", "quarterly", "forecast", "report"]
}

# --- 2. DORK FACTORY i.e the synthesiser ---
def build_query(subject, intent, bank_block, title_block):
    # Subject and Intent
    query = f'("{subject}")'
    if intent:
        query += f' ("{intent}")'
    
    # PDF Filter
    query += ' filetype:pdf'
    
    # Title Block
    if title_block:
        titles = " OR ".join([f'intitle:"{t}"' for t in title_block])
        query += f' ({titles})'
        
    # Bank Block
    if bank_block:
        banks = " OR ".join([f'site:{b}' for b in bank_block])
        query += f' ({banks})'
        
    return query

# --- 3. SERPER MANAGER ---
def fetch_links(query, num_results):
    print(f"   [Search] Query: {query[:80]}...")
    url = "https://google.serper.dev/search"
    payload = {"q": query, "num": num_results}
    headers = {'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json'}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        results = response.json().get('organic', [])
        return [{"url": r['link'], "title": r['title']} for r in results]
    except Exception as e:
        print(f"   ! Search API Error: {e}")
        return []

# --- 4. THE ARCHIVIST (Downloader & Registrar) ---
def download_corpus(subject, intent, candidates):
    # Handle the "no-intent" folder naming logic
    intent_label = intent.replace(" ", "-") if intent else "no-intent"
    folder_name = f"{subject}_{intent_label}_{SEARCH_PARAMS['date_after']}"
    base_path = os.path.join("data", "raw", folder_name)
    os.makedirs(base_path, exist_ok=True)
    
    manifest = []
    
    print(f"   [Download] Saving to: {base_path}")
    
    for i, item in enumerate(candidates):
        report_id = f"{subject.upper()}-{uuid.uuid4().hex[:6]}"
        filename = f"{report_id}.pdf"
        filepath = os.path.join(base_path, filename)
        
        try:
            print(f"      ({i+1}/{len(candidates)}) Downloading {report_id}...", end="\r")
            resp = requests.get(item['url'], timeout=15)
            resp.raise_for_status()
            with open(filepath, 'wb') as f:
                f.write(resp.content)
            
            manifest.append({
                "report_id": report_id,
                "original_title": item['title'],
                "url": item['url'],
                "status": "success",
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            manifest.append({
                "report_id": report_id,
                "url": item['url'],
                "status": f"failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            })

    # Save Manifest
    with open(os.path.join(base_path, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=4)
    print(f"\n   [Done] Manifest saved for {subject}.")

# --- MAIN EXECUTION LOOP ---
if __name__ == "__main__":
    subjects = SEARCH_PARAMS["subjects"]
    if isinstance(subjects, str): subjects = [subjects]
    
    for sub in subjects:
        print(f"\n>>> Starting Job: {sub}")
        query = build_query(
            sub, 
            SEARCH_PARAMS["intent"], 
            SEARCH_PARAMS["bank_block"], 
            SEARCH_PARAMS["title_block"]
        )
        candidates = fetch_links(query, SEARCH_PARAMS["num_results"])
        
        if candidates:
            download_corpus(sub, SEARCH_PARAMS["intent"], candidates)
        else:
            print(f"   ! No candidates found for {sub}")
