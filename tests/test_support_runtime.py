from __future__ import annotations

import json
import logging
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace

from backend.supporting import CrashReporter, configure_logging, install_crash_hooks
from backend.supporting.logging import LOGGER_NAME


class SupportRuntimeTests(unittest.TestCase):
    def tearDown(self):
        logger = logging.getLogger(LOGGER_NAME)
        for handler in tuple(logger.handlers):
            if getattr(handler, "_ai_content_studio_log", False):
                logger.removeHandler(handler)
                handler.close()

    def test_logging_is_json_redacted_and_handler_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            logger, path = configure_logging(directory)
            same_logger, same_path = configure_logging(directory)

            self.assertIs(logger, same_logger)
            self.assertEqual(path, same_path)
            self.assertEqual(
                1,
                sum(
                    bool(getattr(handler, "_ai_content_studio_log", False))
                    for handler in logger.handlers
                ),
            )

            logger.error(
                "api_key=sk-example-secret Authorization: Bearer token-value at %s",
                Path.home() / "private",
            )
            for handler in logger.handlers:
                handler.flush()
            entries = [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
            ]
            record = entries[-1]
            self.assertEqual("ERROR", record["level"])
            self.assertEqual(LOGGER_NAME, record["logger"])
            self.assertNotIn("sk-example-secret", record["message"])
            self.assertNotIn("token-value", record["message"])
            self.assertNotIn(str(Path.home()), record["message"])
            self.assertIn("[REDACTED]", record["message"])

    def test_logging_rotates_at_configured_limit(self):
        with tempfile.TemporaryDirectory() as temporary:
            logger, path = configure_logging(
                temporary,
                max_bytes=180,
                backup_count=2,
            )
            for index in range(20):
                logger.info("rotation record %d %s", index, "x" * 80)
            for handler in logger.handlers:
                handler.flush()

            self.assertTrue(path.is_file())
            self.assertTrue(path.with_name("application.log.1").is_file())
            self.assertLessEqual(
                len(list(Path(temporary).glob("application.log*"))),
                3,
            )

    def test_crash_report_is_redacted_local_and_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            reporter = CrashReporter(directory, max_reports=2)
            for index in range(3):
                try:
                    raise RuntimeError(
                        f"password=secret-{index} in {Path.home() / 'private'}"
                    )
                except RuntimeError:
                    destination = reporter.capture(
                        *sys.exc_info(),
                        thread="worker-api_key=sk-worker-secret",
                    )

            reports = reporter.reports()
            self.assertEqual(2, len(reports))
            self.assertIn(destination, reports)
            payload = json.loads(destination.read_text(encoding="utf-8"))
            serialized = json.dumps(payload)
            self.assertEqual("never automatic", payload["upload"])
            self.assertEqual("RuntimeError", payload["exception_type"])
            self.assertNotIn("secret-2", serialized)
            self.assertNotIn("sk-worker-secret", serialized)
            self.assertNotIn(str(Path.home()), serialized)
            self.assertFalse(list(directory.glob("*.tmp")))

    def test_crash_report_size_failure_leaves_no_partial_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            reporter = CrashReporter(temporary, max_report_bytes=1024)
            try:
                raise RuntimeError("x" * 10000)
            except RuntimeError:
                with self.assertRaisesRegex(ValueError, "size limit"):
                    reporter.capture(*sys.exc_info())

            self.assertEqual((), reporter.reports())
            self.assertFalse(list(Path(temporary).glob("*.tmp")))

    def test_control_flow_exceptions_are_not_reported(self):
        with tempfile.TemporaryDirectory() as temporary:
            reporter = CrashReporter(temporary)
            self.assertIsNone(
                reporter.capture(
                    KeyboardInterrupt,
                    KeyboardInterrupt(),
                    None,
                )
            )
            self.assertFalse(Path(temporary).exists())

    def test_crash_hooks_capture_main_and_thread_then_restore(self):
        calls = []
        previous_main = sys.excepthook
        previous_thread = threading.excepthook

        def main_fallback(exc_type, exc_value, exc_traceback):
            calls.append(("fallback-main", exc_type))

        def thread_fallback(args):
            calls.append(("fallback-thread", args.exc_type))

        class Recorder:
            def capture(self, exc_type, exc_value, exc_traceback, *, thread):
                calls.append(("capture", exc_type, thread))

        sys.excepthook = main_fallback
        threading.excepthook = thread_fallback
        try:
            _, restore = install_crash_hooks(Recorder())
            installed_main = sys.excepthook
            installed_thread = threading.excepthook
            installed_main(RuntimeError, RuntimeError("main"), None)
            installed_thread(
                SimpleNamespace(
                    exc_type=ValueError,
                    exc_value=ValueError("worker"),
                    exc_traceback=None,
                    thread=SimpleNamespace(name="worker-1"),
                )
            )
            restore()

            self.assertIs(sys.excepthook, main_fallback)
            self.assertIs(threading.excepthook, thread_fallback)
            self.assertIn(("capture", RuntimeError, "main"), calls)
            self.assertIn(("fallback-main", RuntimeError), calls)
            self.assertIn(("capture", ValueError, "worker-1"), calls)
            self.assertIn(("fallback-thread", ValueError), calls)
        finally:
            sys.excepthook = previous_main
            threading.excepthook = previous_thread


if __name__ == "__main__":
    unittest.main()
