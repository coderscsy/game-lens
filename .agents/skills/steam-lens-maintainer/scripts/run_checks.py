#!/usr/bin/env python3
"""Build Steam Lens and run reproducible offline checks with honest test reporting.

Python 3.10+, standard library only. Does not install dependencies or access live
Steam. Build updates steam_lens.html/demo_data.json; browser tests update their
existing result JSON. Use --browser to request the two Playwright suites.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

REQUIRED = ('app.js', 'ui.template.html', 'build.py', 'server.py',
            'test_server.py', 'test_frontend.py', 'test_covers.py')
COUNT_PATTERNS = {
    'backend': r'Ran (\d+) tests?\b',
    'frontend': r'(\d+) frontend checks passed',
    'covers': r'(\d+) cover checks passed',
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd(), help='Steam Lens project root.')
    parser.add_argument('--browser', action='store_true', help='Run frontend and cover browser tests.')
    parser.add_argument('--timeout', type=int, default=180, help='Seconds per command (default: 180).')
    args = parser.parse_args()
    root = args.root.expanduser().resolve()
    if args.timeout <= 0:
        parser.error('--timeout must be positive.')
    missing = [name for name in REQUIRED if not (root / name).is_file()]
    if missing:
        parser.error('Missing project files: ' + ', '.join(missing))
    now = datetime.now(timezone.utc)
    report_dir = root / '.codex-checks' / now.strftime('%Y%m%dT%H%M%S%fZ')
    report_dir.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    env.setdefault('TERM', 'dumb')
    results: list[dict] = []

    def skipped(name: str, reason: str, unavailable: bool = False) -> None:
        results.append({'name': name, 'status': 'unavailable' if unavailable else 'skipped',
                        'reason': reason, 'command': [], 'duration_seconds': 0,
                        'exit_code': None, 'checks': None, 'log': None})
        print(f"{results[-1]['status'].upper()}: {name}: {reason}")

    def run(name: str, command: list[str], detect_browser_missing: bool = False) -> bool:
        started = time.monotonic()
        print(f'RUN: {name}', flush=True)
        status = 'failed'
        exit_code: int | None = None
        output = ''
        try:
            completed = subprocess.run(
                command, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='replace', timeout=args.timeout, check=False,
            )
            output, exit_code = completed.stdout, completed.returncode
            status = 'passed' if exit_code == 0 else 'failed'
            if detect_browser_missing and exit_code != 0 and (
                "Executable doesn't exist" in output
                or 'executable doesn\'t exist' in output.lower()
                or 'browserType.launch: Failed to launch' in output
                or 'Host system is missing dependencies' in output
            ):
                status = 'unavailable'
        except subprocess.TimeoutExpired as exc:
            raw = exc.stdout or ''
            output = raw.decode('utf-8', errors='replace') if isinstance(raw, bytes) else raw
            output += f'\nTIMEOUT: exceeded {args.timeout} seconds.\n'
        except OSError as exc:
            output = str(exc)
            status = 'unavailable'
        elapsed = round(time.monotonic() - started, 3)
        log_name = name + '.log'
        (report_dir / log_name).write_text(output, encoding='utf-8')
        pattern = COUNT_PATTERNS.get(name)
        found = re.search(pattern, output) if pattern else None
        count = int(found.group(1)) if found and status == 'passed' else None
        results.append({'name': name, 'status': status, 'command': command,
                        'exit_code': exit_code, 'duration_seconds': elapsed,
                        'checks': count, 'log': log_name})
        print(f'{status.upper()}: {name} ({elapsed}s)' +
              (f' / {count} checks' if count is not None else ''))
        if status != 'passed':
            print(output[-2500:])
        return status == 'passed'

    build_ok = run('build', [sys.executable, 'build.py'])
    run('python-syntax', [sys.executable, '-m', 'py_compile',
                         'build.py', 'server.py', 'test_server.py',
                         'test_frontend.py', 'test_covers.py'])
    node = shutil.which('node')
    if node:
        run('javascript-syntax', [node, '--check', 'app.js'])
    else:
        skipped('javascript-syntax', 'Node is not installed or not on PATH.', unavailable=True)
    run('backend', [sys.executable, '-W', 'error::ResourceWarning', '-m', 'unittest', '-v', 'test_server.py'])
    if not args.browser:
        for suite in ('frontend', 'covers'):
            skipped(suite, 'Not requested. Pass --browser for complete offline regression.')
    elif not build_ok:
        for suite in ('frontend', 'covers'):
            skipped(suite, 'Build failed; do not validate stale generated HTML.')
    elif importlib.util.find_spec('playwright') is None:
        for suite in ('frontend', 'covers'):
            skipped(suite, 'Playwright is not installed for this Python interpreter.', unavailable=True)
    else:
        for suite, filename in (('frontend', 'test_frontend.py'), ('covers', 'test_covers.py')):
            run(suite, [sys.executable, filename], detect_browser_missing=True)

    failed = any(item['status'] == 'failed' for item in results)
    unavailable = any(item['status'] == 'unavailable' for item in results)
    code = 1 if failed else 2 if unavailable else 0
    report = {
        'generated_at_utc': now.isoformat(), 'project_root': str(root),
        'python': sys.version.split()[0], 'browser_requested': args.browser,
        'exit_code': code,
        'full_offline_regression_passed': args.browser and all(x['status'] == 'passed' for x in results),
        'live_steam_verified': False,
        'notes': ['Steam upstream responses and images are mocked by the baseline tests.',
                  'Passing offline tests does not verify real Steam/CDN availability.'],
        'results': results,
    }
    (report_dir / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    lines = ['# Steam Lens offline check report', '',
             f"UTC: {report['generated_at_utc']}",
             f'Exit code: {code}',
             f"Complete offline regression passed: {report['full_offline_regression_passed']}",
             'Live Steam/CDN verified: **No**', '',
             '| Check | Status | Count | Log |', '| --- | --- | --- | --- |']
    for item in results:
        count = str(item['checks']) if item['checks'] is not None else '-'
        log = f"[{item['log']}]({item['log']})" if item['log'] else item.get('reason', '-')
        lines.append(f"| {item['name']} | {item['status']} | {count} | {log} |")
    lines += ['', 'Browser checks use mock upstream responses and synthetic images. '
              'Missing dependencies and skipped suites are not passes.', '']
    (report_dir / 'report.md').write_text('\n'.join(lines), encoding='utf-8')
    print(f'Report: {report_dir / "report.md"}')
    print('Live Steam/CDN verified: NO')
    return code


if __name__ == '__main__':
    raise SystemExit(main())
