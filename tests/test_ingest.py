"""Contract checks using the actual synthetic corpus, without API calls."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ingest import PROJECT_ROOT, ingest


class IngestionTests(unittest.TestCase):
    def test_corpus_is_complete_traceable_and_repeatable(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT, prefix=".test-") as temporary:
            output = Path(temporary) / "processed"
            manifest = ingest(PROJECT_ROOT / "data" / "raw", output)
            self.assertEqual(manifest["document_count"], 6)
            self.assertEqual(manifest["page_count"], 26)
            first_run = (output / "pages.jsonl").read_bytes()
            records = [json.loads(line) for line in first_run.decode().splitlines()]
            self.assertEqual(len({row["record_id"] for row in records}), 26)
            for row in records:
                metadata = row["metadata"]
                original = PROJECT_ROOT / "data" / "raw" / metadata["source"]
                self.assertEqual(metadata["source_sha256"], hashlib.sha256(original.read_bytes()).hexdigest())
                self.assertTrue(metadata["synthetic"])
                self.assertGreater(metadata["page"], 0)
                self.assertIn("NOT REAL DOH DATA", row["text"])
            claims = "\n".join(row["text"] for row in records if row["metadata"]["doc_id"] == "FWA-01")
            self.assertIn("PRV00092", claims)
            self.assertIn("12,000 SCU", claims)
            ingest(PROJECT_ROOT / "data" / "raw", output)
            self.assertEqual(first_run, (output / "pages.jsonl").read_bytes())

    def test_empty_input_does_not_replace_previous_output(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT, prefix=".test-") as temporary:
            root = Path(temporary)
            (root / "raw").mkdir()
            (root / "processed").mkdir()
            previous = root / "processed" / "pages.jsonl"
            previous.write_text("previous successful run", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "No PDF files"):
                ingest(root / "raw", root / "processed")
            self.assertEqual(previous.read_text(), "previous successful run")

    def test_corrupt_pdf_does_not_publish_partial_batch(self):
        with tempfile.TemporaryDirectory(dir=PROJECT_ROOT, prefix=".test-") as temporary:
            root = Path(temporary)
            raw = root / "raw"
            raw.mkdir()
            first = sorted((PROJECT_ROOT / "data" / "raw").glob("*.pdf"))[0]
            (raw / first.name).write_bytes(first.read_bytes())
            (raw / "fwa_99_corrupt.pdf").write_bytes(b"not a PDF")
            with self.assertRaises(Exception):
                ingest(raw, root / "processed")
            self.assertFalse((root / "processed" / "pages.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
