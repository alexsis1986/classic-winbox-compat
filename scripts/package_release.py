#!/usr/bin/env python3
"""Reproducible source-only ZIP builder. Never package official WinBox binaries."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
import re
import zipfile

ROOT = Path(__file__).resolve().parent.parent
RELEASE_FILES = (
    '01_BUILD_WINBOX.cmd', '02_RUN_WINBOX.cmd', '03_VERIFY_FILES.cmd',
    'WinBox-Toolkit.ps1', 'build_winbox.py', 'scripts/import_upstream.py', 'SHA256SUMS.txt',
    'NOTICE.txt', 'BUILD_STATUS.json', 'README_RU.txt', 'VALIDATION_REPORT_RU.txt',
    'README.md', 'README.ru.md', 'CHANGELOG.md', 'CONTRIBUTING.md', 'SECURITY.md',
    'LICENSE', 'docs/COMPATIBILITY.md', 'docs/LEGAL.md',
    'source/PLACE_ORIGINAL_HERE.txt', 'source/icons/PLACE_ICONS_HERE.txt',
    'tests/test_builder.py', 'tests/unit-tests.txt',
)
BLOCKED_EXTENSIONS = {'.exe', '.dll', '.png', '.rif', '.npk', '.backup', '.rsc', '.pfx', '.pem'}

def make_zip(tag: str, output: Path) -> None:
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,60}', tag):
        raise ValueError('Unsafe release tag')
    files = [ROOT / name for name in RELEASE_FILES]
    for p in files:
        if not p.is_file() or p.is_symlink() or p.suffix.lower() in BLOCKED_EXTENSIONS:
            raise ValueError(f'Missing or forbidden release file: {p}')
    output.parent.mkdir(parents=True, exist_ok=True)
    prefix = f'ClassicWinBoxCompat-{tag}/'
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for filename, p in sorted(zip(RELEASE_FILES, files)):
            entry = zipfile.ZipInfo(prefix + filename, date_time=(2026, 10, 31, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            entry.external_attr = 0o644 << 16
            z.writestr(entry, p.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(output) as z:
        names = z.namelist()
        if len(names) != len(RELEASE_FILES) or len(set(names)) != len(names):
            raise RuntimeError('ZIP manifest mismatch')
        if any(Path(name).suffix.lower() in BLOCKED_EXTENSIONS for name in names):
            raise RuntimeError('Forbidden executable or artwork detected')
        bad = z.testzip()
        if bad:
            raise RuntimeError(f'ZIP CRC mismatch: {bad}')
    sha = hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_name(output.name + '.sha256').write_text(f'{sha}  {output.name}\n', encoding='ascii')
    print(f'PACKAGED: {output}')
    print(f'FILES: {len(RELEASE_FILES)} / no WinBox executable or icons')
    print(f'SHA-256: {sha}')

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--tag', default='v1.0.0')
    ap.add_argument('--output', type=Path, default=ROOT/'dist/ClassicWinBoxCompat-v1.0.0.zip')
    a = ap.parse_args()
    make_zip(a.tag, a.output)
