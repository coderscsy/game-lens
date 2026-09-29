#!/usr/bin/env python3
"""Restore the verified Steam Lens baseline into a NEW directory; never overwrite.

Python 3.10+, standard library only. No network, installation, Git or Steam actions.
The original 18 source files are restored byte-for-byte. The Skill and handoff
notes are added alongside the source. Existing projects should copy the Skill
manually instead of running this script over their source tree.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import zipfile

SKILL = Path(__file__).resolve().parents[1]
ASSETS = SKILL / 'assets'
MAX_UNCOMPRESSED = 20 * 1024 * 1024


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verified_payload() -> dict[str, bytes]:
    """Validate archive identity and every entry before creating a destination."""
    manifest = json.loads((ASSETS / 'baseline-manifest.json').read_text(encoding='utf-8'))
    archive_name = manifest.get('archive')
    if archive_name != 'steam-lens-v1.1-baseline.zip':
        raise ValueError('Unexpected baseline archive name.')
    archive = ASSETS / archive_name
    if sha256(archive.read_bytes()) != manifest['archive_sha256']:
        raise ValueError('Baseline ZIP SHA-256 mismatch; refusing to restore.')
    expected = manifest.get('baseline_files')
    if not isinstance(expected, dict) or not expected:
        raise ValueError('Missing baseline file manifest.')
    files: dict[str, bytes] = {}
    total = 0
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            name = info.filename
            part = PurePosixPath(name)
            mode = info.external_attr >> 16
            if ('\\' in name or part.is_absolute() or '..' in part.parts
                    or any(':' in item for item in part.parts)
                    or not part.parts or part.parts[0] != 'steam-lens'
                    or stat.S_ISLNK(mode)):
                raise ValueError(f'Unsafe archive entry: {name!r}')
            if info.is_dir():
                continue
            relative = PurePosixPath(*part.parts[1:]).as_posix()
            if relative in files or relative not in expected:
                raise ValueError(f'Unexpected or duplicate archive file: {name!r}')
            total += info.file_size
            if total > MAX_UNCOMPRESSED:
                raise ValueError('Baseline archive exceeds extraction size limit.')
            data = zf.read(info)
            if sha256(data) != expected[relative]:
                raise ValueError(f'Baseline file SHA-256 mismatch: {relative}')
            files[relative] = data
    if set(files) != set(expected):
        raise ValueError('Baseline archive has missing files.')
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dest', required=True, help='New project directory; must not exist.')
    args = parser.parse_args()
    # Reject existing symlinks (including broken ones) before resolving the path.
    requested = Path(args.dest).expanduser().absolute()
    if os.path.lexists(requested):
        parser.error(f'Destination already exists; no files changed: {requested}')
    dest = requested.resolve()
    if dest.is_relative_to(SKILL):
        parser.error('Destination must be outside the Skill folder.')
    try:
        files = verified_payload()
        # Never follow links while copying the installed Skill.
        for item in SKILL.rglob('*'):
            if item.is_symlink():
                raise ValueError(f'Skill contains a symlink: {item.relative_to(SKILL)}')
        for name in ('AGENTS.md', 'CODEX_START_PROMPT.md', 'START_HERE_中文.md'):
            if not (ASSETS / name).is_file():
                raise ValueError(f'Missing handoff template: {name}')
        dest.parent.mkdir(parents=True, exist_ok=True)
        # mkdir(exist_ok=False) also protects against an intervening creation.
        dest.mkdir(exist_ok=False)
        for relative, data in files.items():
            target = dest / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as stream:
                stream.write(data)
        shutil.copytree(
            SKILL, dest / '.agents' / 'skills' / 'steam-lens-maintainer',
            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'),
        )
        for name in ('AGENTS.md', 'CODEX_START_PROMPT.md', 'START_HERE_中文.md'):
            with (dest / name).open('xb') as stream:
                stream.write((ASSETS / name).read_bytes())
        (dest / '.gitignore').write_text(
            '__pycache__/\n*.py[cod]\n.venv/\n.conda/\n'
            '.steam_lens_cache.sqlite3*\n.codex-checks/\n.DS_Store\n',
            encoding='utf-8',
        )
        for name in ('start_mac.command', 'start_linux.sh'):
            (dest / name).chmod(0o755)
        print(f'Restored {len(files)} verified baseline files into: {dest}')
        print('Added project Skill, AGENTS.md and Chinese handoff instructions.')
        print('Open this directory in Codex; use $steam-lens-maintainer.')
        print('No dependencies installed. No real Steam connectivity tested.')
        return 0
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        if dest.exists():
            print('A partial NEW directory may remain; inspect it before retrying. '
                  'No pre-existing project was intentionally overwritten.', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
