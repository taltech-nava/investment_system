from __future__ import annotations

import asyncio
import csv
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("LLM_PROVIDER", "openai")
os.environ.setdefault("LLM_MODEL", "gpt-4o-mini")


def _make_auditor(raw_dir: str, proc_dir: str) -> "Auditor":
    from src.ingestion.auditor import Auditor

    auditor = Auditor.__new__(Auditor)
    auditor.raw_dir = raw_dir
    auditor.proc_dir = proc_dir
    auditor.final_dir = os.path.join(proc_dir, "final")
    auditor.blocked_dir = os.path.join(proc_dir, "blocked")
    auditor.log_file = os.path.join(proc_dir, "audit_trail.csv")
    os.makedirs(auditor.final_dir, exist_ok=True)
    os.makedirs(auditor.blocked_dir, exist_ok=True)
    auditor.broker = MagicMock()
    return auditor


@pytest.fixture
def tmp_dirs() -> tuple[str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        raw = os.path.join(tmp, "raw")
        proc = os.path.join(tmp, "proc")
        os.makedirs(raw)
        os.makedirs(proc)
        yield raw, proc


class TestLocalTriage:
    def test_passes_valid_pdf(self, tmp_dirs: tuple[str, str]) -> None:
        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)
        path = os.path.join(raw, "test.pdf")
        Path(path).write_bytes(b"x" * 2048)

        assert auditor.local_triage("test.pdf") is True

    def test_blocks_missing_file(self, tmp_dirs: tuple[str, str]) -> None:
        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)

        assert auditor.local_triage("missing.pdf") is False

    def test_blocks_file_under_1kb(self, tmp_dirs: tuple[str, str]) -> None:
        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)
        path = os.path.join(raw, "tiny.pdf")
        Path(path).write_bytes(b"x" * 100)

        assert auditor.local_triage("tiny.pdf") is False

    def test_logs_warning_for_missing_file(
        self, tmp_dirs: tuple[str, str], caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)

        with caplog.at_level(logging.WARNING, logger="src.ingestion.auditor"):
            auditor.local_triage("missing.pdf")

        assert any("not found" in r.message for r in caplog.records)

    def test_logs_warning_for_tiny_file(
        self, tmp_dirs: tuple[str, str], caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)
        Path(os.path.join(raw, "tiny.pdf")).write_bytes(b"x" * 100)

        with caplog.at_level(logging.WARNING, logger="src.ingestion.auditor"):
            auditor.local_triage("tiny.pdf")

        assert any("too small" in r.message for r in caplog.records)


class TestLogResult:
    def test_writes_csv_row(self, tmp_dirs: tuple[str, str]) -> None:
        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)

        auditor.log_result("RPT-001", 4, "final", "good report")

        with open(auditor.log_file) as f:
            rows = list(csv.reader(f))

        assert rows[0] == ["report_id", "score", "status", "reasoning"]
        assert rows[1] == ["RPT-001", "4", "final", "good report"]

    def test_appends_without_duplicate_header(self, tmp_dirs: tuple[str, str]) -> None:
        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)

        auditor.log_result("RPT-001", 4, "final", "first")
        auditor.log_result("RPT-002", 2, "blocked", "second")

        with open(auditor.log_file) as f:
            rows = list(csv.reader(f))

        headers = [r for r in rows if r[0] == "report_id"]
        assert len(headers) == 1
        assert len(rows) == 3

    def test_logs_result_to_app_logger(
        self, tmp_dirs: tuple[str, str], caplog: pytest.LogCaptureFixture
    ) -> None:
        import logging

        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)

        with caplog.at_level(logging.INFO, logger="src.ingestion.auditor"):
            auditor.log_result("RPT-001", 4, "final", "good")

        assert any("RPT-001" in r.message for r in caplog.records)


class TestProcessFile:
    def _make_file_meta(self, report_id: str) -> dict:
        return {"report_id": report_id}

    def test_blocks_when_local_triage_fails(self, tmp_dirs: tuple[str, str]) -> None:
        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)

        asyncio.run(
            auditor.process_file(self._make_file_meta("MISSING-001"), asyncio.Semaphore(1))
        )

        with open(auditor.log_file) as f:
            rows = list(csv.reader(f))
        assert any("MISSING-001" in r and "blocked" in r for r in rows[1:])

    def test_blocks_when_pdf_read_fails(self, tmp_dirs: tuple[str, str]) -> None:
        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)
        Path(os.path.join(raw, "BAD-001.pdf")).write_bytes(b"x" * 2048)

        with patch.object(auditor, "get_pdf_text", return_value="Error: corrupt"):
            asyncio.run(
                auditor.process_file(self._make_file_meta("BAD-001"), asyncio.Semaphore(1))
            )

        with open(auditor.log_file) as f:
            rows = list(csv.reader(f))
        assert any("BAD-001" in r and "blocked" in r for r in rows[1:])

    def test_moves_to_final_when_score_passes(self, tmp_dirs: tuple[str, str]) -> None:
        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)
        Path(os.path.join(raw, "RPT-001.pdf")).write_bytes(b"x" * 2048)

        good_vote = json.dumps({"is_report": True, "score": 4, "reasoning": "solid", "type": "research"})
        auditor.broker.ask_batch = AsyncMock(return_value=[good_vote] * 5)

        with patch.object(auditor, "get_pdf_text", return_value="some text"):
            asyncio.run(
                auditor.process_file(self._make_file_meta("RPT-001"), asyncio.Semaphore(1))
            )

        assert os.path.exists(os.path.join(proc, "final", "RPT-001.pdf"))

    def test_moves_to_blocked_when_score_fails(self, tmp_dirs: tuple[str, str]) -> None:
        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)
        Path(os.path.join(raw, "SPAM-001.pdf")).write_bytes(b"x" * 2048)

        bad_vote = json.dumps({"is_report": False, "score": 1, "reasoning": "spam", "type": "spam"})
        auditor.broker.ask_batch = AsyncMock(return_value=[bad_vote] * 5)

        with patch.object(auditor, "get_pdf_text", return_value="some text"):
            asyncio.run(
                auditor.process_file(self._make_file_meta("SPAM-001"), asyncio.Semaphore(1))
            )

        assert os.path.exists(os.path.join(proc, "blocked", "SPAM-001.pdf"))

    def test_blocks_when_all_votes_malformed(self, tmp_dirs: tuple[str, str]) -> None:
        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)
        Path(os.path.join(raw, "RPT-002.pdf")).write_bytes(b"x" * 2048)

        auditor.broker.ask_batch = AsyncMock(return_value=["not json"] * 5)

        with patch.object(auditor, "get_pdf_text", return_value="some text"):
            asyncio.run(
                auditor.process_file(self._make_file_meta("RPT-002"), asyncio.Semaphore(1))
            )

        with open(auditor.log_file) as f:
            rows = list(csv.reader(f))
        assert any("RPT-002" in r and "blocked" in r for r in rows[1:])

    def test_majority_vote_determines_outcome(self, tmp_dirs: tuple[str, str]) -> None:
        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)
        Path(os.path.join(raw, "RPT-003.pdf")).write_bytes(b"x" * 2048)

        votes = (
            [json.dumps({"score": 2, "reasoning": "low", "is_report": False, "type": "news"})] * 3
            + [json.dumps({"score": 4, "reasoning": "good", "is_report": True, "type": "research"})] * 2
        )
        auditor.broker.ask_batch = AsyncMock(return_value=votes)

        with patch.object(auditor, "get_pdf_text", return_value="some text"):
            asyncio.run(
                auditor.process_file(self._make_file_meta("RPT-003"), asyncio.Semaphore(1))
            )

        assert os.path.exists(os.path.join(proc, "blocked", "RPT-003.pdf"))

    def test_passes_calling_module_to_broker(self, tmp_dirs: tuple[str, str]) -> None:
        raw, proc = tmp_dirs
        auditor = _make_auditor(raw, proc)
        Path(os.path.join(raw, "RPT-004.pdf")).write_bytes(b"x" * 2048)

        good_vote = json.dumps({"score": 4, "reasoning": "ok", "is_report": True, "type": "research"})
        auditor.broker.ask_batch = AsyncMock(return_value=[good_vote] * 5)

        with patch.object(auditor, "get_pdf_text", return_value="text"):
            asyncio.run(
                auditor.process_file(self._make_file_meta("RPT-004"), asyncio.Semaphore(1))
            )

        call_kwargs = auditor.broker.ask_batch.call_args[1]
        assert call_kwargs.get("calling_module") == "auditor"
