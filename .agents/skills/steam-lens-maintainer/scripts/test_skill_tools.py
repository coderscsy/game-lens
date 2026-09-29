"""Standard-library tests for handoff tools; does not exercise live Steam."""
from __future__ import annotations

from contextlib import redirect_stdout, redirect_stderr
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import bootstrap_project as bootstrap
import run_checks as runner


class BootstrapTests(unittest.TestCase):
    def test_real_payload_matches_every_hash(self):
        files = bootstrap.verified_payload()
        manifest = json.loads((bootstrap.ASSETS / 'baseline-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(set(files), set(manifest['baseline_files']))
        for name, data in files.items():
            self.assertEqual(hashlib.sha256(data).hexdigest(), manifest['baseline_files'][name])

    def test_fresh_restore_installs_skill_and_keeps_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'new'
            with patch.object(sys, 'argv', ['bootstrap', '--dest', str(dest)]), redirect_stdout(io.StringIO()):
                self.assertEqual(bootstrap.main(), 0)
            self.assertTrue((dest / '.agents/skills/steam-lens-maintainer/SKILL.md').is_file())
            self.assertTrue((dest / 'CODEX_START_PROMPT.md').is_file())
            for name, data in bootstrap.verified_payload().items():
                self.assertEqual((dest / name).read_bytes(), data)

    def test_existing_directory_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp)
            sentinel = dest / 'app.js'
            sentinel.write_text('USER CHANGES', encoding='utf-8')
            with patch.object(sys, 'argv', ['bootstrap', '--dest', str(dest)]), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:
                    bootstrap.main()
            self.assertEqual(raised.exception.code, 2)
            self.assertEqual(sentinel.read_text(), 'USER CHANGES')
            self.assertEqual(len(list(dest.iterdir())), 1)

    def test_empty_existing_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(sys, 'argv', ['bootstrap', '--dest', tmp]), redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    bootstrap.main()
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_destination_inside_skill_is_refused(self):
        dest = bootstrap.SKILL / 'must-never-be-created-by-test'
        with patch.object(sys, 'argv', ['bootstrap', '--dest', str(dest)]), redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                bootstrap.main()
        self.assertFalse(dest.exists())

    def test_tampered_archive_rejected_before_restore(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets = Path(tmp)
            manifest = json.loads((bootstrap.ASSETS / 'baseline-manifest.json').read_text(encoding='utf-8'))
            (assets / 'baseline-manifest.json').write_text(json.dumps(manifest))
            (assets / manifest['archive']).write_bytes(b'not the baseline')
            with patch.object(bootstrap, 'ASSETS', assets):
                with self.assertRaisesRegex(ValueError, 'SHA-256'):
                    bootstrap.verified_payload()

    def test_path_traversal_rejected_even_with_matching_zip_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            assets = Path(tmp)
            archive = assets / 'steam-lens-v1.1-baseline.zip'
            with zipfile.ZipFile(archive, 'w') as zf:
                zf.writestr('steam-lens/../../escape.txt', 'evil')
            manifest = {'archive': archive.name, 'archive_sha256': hashlib.sha256(archive.read_bytes()).hexdigest(),
                        'baseline_files': {'../../escape.txt': hashlib.sha256(b'evil').hexdigest()}}
            (assets / 'baseline-manifest.json').write_text(json.dumps(manifest))
            with patch.object(bootstrap, 'ASSETS', assets):
                with self.assertRaisesRegex(ValueError, 'Unsafe'):
                    bootstrap.verified_payload()


class RunnerTests(unittest.TestCase):
    def exercise(self, browser=False, node=True, build_fail=False, playwright=True):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in runner.REQUIRED:
                (root / name).write_text('', encoding='utf-8')
            argv = ['checks', '--root', str(root)] + (['--browser'] if browser else [])
            def fake_run(command, **kwargs):
                if command[-1] == 'build.py' and build_fail:
                    return subprocess.CompletedProcess(command, 1, 'build failed')
                if command[-1] == 'test_server.py' and 'unittest' in command:
                    out = 'Ran 3 tests in 0.1s\nOK'
                elif command[-1] == 'test_frontend.py':
                    out = '5 frontend checks passed'
                elif command[-1] == 'test_covers.py':
                    out = '2 cover checks passed'
                else:
                    out = 'OK'
                return subprocess.CompletedProcess(command, 0, out)
            with patch.object(sys, 'argv', argv), patch.object(runner.shutil, 'which', return_value='node' if node else None), \
                 patch.object(runner.importlib.util, 'find_spec', return_value=object() if playwright else None), \
                 patch.object(runner.subprocess, 'run', side_effect=fake_run), redirect_stdout(io.StringIO()):
                code = runner.main()
            report_path = next(root.glob('.codex-checks/*/report.json'))
            return code, json.loads(report_path.read_text(encoding='utf-8'))

    def test_optional_browser_skip_is_not_full_pass(self):
        code, report = self.exercise()
        self.assertEqual(code, 0)
        self.assertFalse(report['full_offline_regression_passed'])
        self.assertFalse(report['live_steam_verified'])
        self.assertEqual(report['results'][-1]['status'], 'skipped')

    def test_missing_node_is_unavailable_not_passed(self):
        code, report = self.exercise(node=False)
        self.assertEqual(code, 2)
        self.assertIn('unavailable', [x['status'] for x in report['results']])

    def test_full_run_records_actual_counts_not_baseline_constants(self):
        code, report = self.exercise(browser=True)
        self.assertEqual(code, 0)
        self.assertTrue(report['full_offline_regression_passed'])
        counts = {x['name']: x['checks'] for x in report['results']}
        self.assertEqual((counts['backend'], counts['frontend'], counts['covers']), (3, 5, 2))

    def test_build_failure_prevents_stale_html_browser_tests(self):
        code, report = self.exercise(browser=True, build_fail=True)
        self.assertEqual(code, 1)
        self.assertFalse(report['full_offline_regression_passed'])
        self.assertEqual(report['results'][-1]['status'], 'skipped')

    def test_missing_playwright_is_unavailable_not_passed(self):
        code, report = self.exercise(browser=True, playwright=False)
        self.assertEqual(code, 2)
        self.assertEqual(report['results'][-1]['status'], 'unavailable')


if __name__ == '__main__':
    unittest.main(verbosity=2)
