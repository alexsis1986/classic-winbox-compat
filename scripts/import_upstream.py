#!/usr/bin/env python3
"""Download *text* (never execute it) from a pinned upstream commit and extract patch metadata.

Patch machine code belongs to its respective author(s) and is not stored in this
repository or distributed in its ZIP. This local import must be user-initiated;
installation is not a license grant. All hashes are checked before using data.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_COMMIT = 'b22d97ee6fb222e14ff35151634bdac42a9f5d29'
UPSTREAM_URL = ('https://raw.githubusercontent.com/rodenasl/winbox3-ros7-patch/'
                + UPSTREAM_COMMIT + '/patch_winbox.py')
UPSTREAM_BLOB_SHA1 = 'a2a92d01984e76c6ecd55f04b72d010b2981064b'
PATCH_FINGERPRINT = 'efb2320a1b7283af148114943efc6ae2ccb7cb5754c5b95ccede07454eba227c'
INPUT_HASH = '5b41cf51fd81e8d082687f6b522159cf4aba22e6df8edc486721d4e09507b6e9'
OUTPUT_HASH = 'ac40890431762b588a7b7777d1ad48c54751dbfa2a3868450222dce757ec496d'
FILE_SIZE = 2295976
PATCH_RE = re.compile(r"\(\s*(0x[0-9a-f]+)\s*,\s*(?:(0x[0-9a-f]+)|None)\s*,\s*'([0-9a-f]+)'\s*,\s*'([0-9a-f]+)'\s*\)", re.I | re.S)


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def site_fingerprint(patches: list[dict]) -> str:
    value = '\n'.join(f"{p['offset'].lower()}|{p['before'].lower()}|{p['after'].lower()}" for p in patches)
    return hashlib.sha256(value.encode('ascii')).hexdigest()


def parse_upstream(raw: bytes) -> dict:
    if git_blob_sha1(raw) != UPSTREAM_BLOB_SHA1:
        raise ValueError('Pinned upstream Git blob SHA-1 mismatch; refusing to parse data')
    source = raw.decode('utf-8', errors='strict')
    matches = list(PATCH_RE.finditer(source))
    if len(matches) != 20:
        raise ValueError(f'Expected 20 patch sites, got {len(matches)}')
    headings = list(re.finditer(r"Patch\('([^']+)'", source))
    patches = []
    head = -1
    for match in matches:
        while head + 1 < len(headings) and headings[head+1].start() < match.start():
            head += 1
        if head < 0:
            raise ValueError('Patch site outside a declared patch group')
        offset, va, before, after = match.groups()
        patches.append(dict(id=headings[head].group(1), offset=offset.lower(),
                            va=(va.lower() if va else None), before=before.lower(), after=after.lower()))
    if len({p['id'] for p in patches}) != 12:
        raise ValueError('Unexpected patch group count')
    if site_fingerprint(patches) != PATCH_FINGERPRINT:
        raise ValueError('Unexpected upstream patch-site fingerprint')
    return dict(format_version=1, upstream_repository='https://github.com/rodenasl/winbox3-ros7-patch',
                upstream_commit=UPSTREAM_COMMIT, upstream_patch_file_git_blob_sha1=UPSTREAM_BLOB_SHA1,
                input_sha256=INPUT_HASH, output_sha256=OUTPUT_HASH, file_size=FILE_SIZE,
                patches=patches)


def import_manifest(destination: Path = ROOT / 'source' / 'patches.json') -> Path:
    # No direct execution of downloaded text. URL uses a pinned full commit SHA.
    with urlopen(UPSTREAM_URL, timeout=25) as response:
        raw = response.read(200000)
    manifest = parse_upstream(raw)
    dest = destination.resolve()
    if dest.exists():
        cached = json.loads(dest.read_text(encoding='utf-8-sig'))
        if site_fingerprint(cached['patches']) != PATCH_FINGERPRINT:
            raise ValueError('Existing local manifest has unexpected patch bytes; refusing overwrite')
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(manifest, ensure_ascii=True, indent=2) + '\n').encode('utf-8')
    with tempfile.NamedTemporaryFile(prefix='.manifest-', suffix='.tmp', dir=dest.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, dest)  # fail safely if another process creates it first
    finally:
        temporary.unlink(missing_ok=True)
    return dest


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, default=ROOT / 'source' / 'patches.json')
    args = ap.parse_args()
    try:
        print('Imported verified upstream patch metadata into:', import_manifest(args.output))
        print('The upstream script was read as data only; it was NOT executed.')
    except Exception as e:
        ap.exit(1, f'IMPORT STOPPED: {e}\n')
