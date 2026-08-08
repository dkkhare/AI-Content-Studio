from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.release_evidence import (
    REQUIRED_GATES,
    build_evidence,
    main,
    parse_gate,
    write_evidence,
)


class ReleaseEvidenceTests(unittest.TestCase):
    def test_missing_gates_are_pending_and_candidate_is_not_ready(self):
        evidence = build_evidence(
            commit="abc123",
            version="1.0.0",
            gates=(("project_lifecycle", "pass"),),
            generated_at="2026-01-01T00:00:00+00:00",
        )
        self.assertFalse(evidence["ready"])
        self.assertEqual("pass", evidence["gates"]["project_lifecycle"])
        self.assertEqual("pending", evidence["gates"]["windows_installer"])
        self.assertEqual(set(REQUIRED_GATES), set(evidence["gates"]))

    def test_all_required_gates_make_candidate_ready(self):
        evidence = build_evidence(
            commit="abc123",
            version="1.0.0",
            gates=((name, "pass") for name in REQUIRED_GATES),
        )
        self.assertTrue(evidence["ready"])

    def test_failed_gate_prevents_readiness(self):
        gates = [(name, "pass") for name in REQUIRED_GATES]
        gates[-1] = ("windows_installer", "fail")
        evidence = build_evidence(
            commit="abc123",
            version="1.0.0",
            gates=gates,
        )
        self.assertFalse(evidence["ready"])
        self.assertEqual("fail", evidence["gates"]["windows_installer"])

    def test_gate_parser_rejects_unknown_names_and_statuses(self):
        self.assertEqual(
            ("safe_updates", "pass"),
            parse_gate("safe_updates=pass"),
        )
        for value in ("unknown=pass", "safe_updates=green", "safe_updates"):
            with self.assertRaises(Exception):
                parse_gate(value)

    def test_evidence_write_is_atomic(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "release-evidence.json"
            evidence = build_evidence(
                commit="abc123",
                version="1.0.0",
                gates=(),
            )
            self.assertEqual(output, write_evidence(output, evidence))
            self.assertEqual(
                evidence,
                json.loads(output.read_text(encoding="utf-8")),
            )
            self.assertFalse(output.with_suffix(".json.tmp").exists())

    def test_require_ready_returns_failure_but_preserves_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "evidence.json"
            result = main(
                [
                    "--output",
                    str(output),
                    "--commit",
                    "abc123",
                    "--version",
                    "1.0.0",
                    "--require-ready",
                ]
            )
            self.assertEqual(1, result)
            self.assertFalse(json.loads(output.read_text())["ready"])


if __name__ == "__main__":
    unittest.main()
