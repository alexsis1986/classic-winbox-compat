#!/usr/bin/env python3
"""Fail-closed WinBox 3.43 x64 patch builder (Python 3.9+).

Normal Windows usage: 01_BUILD_WINBOX.cmd; Python is an optional alternative.
Patch metadata is locally imported from the pinned upstream repository.
This independently written builder never overwrites its source or runs an EXE.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import sys
import tempfile
from typing import Any

INPUT_HASH = '5b41cf51fd81e8d082687f6b522159cf4aba22e6df8edc486721d4e09507b6e9'
OUTPUT_HASH = 'ac40890431762b588a7b7777d1ad48c54751dbfa2a3868450222dce757ec496d'
EXPECTED_SIZE = 2295976
from scripts.import_upstream import PATCH_FINGERPRINT, site_fingerprint, import_manifest
ROOT = Path(__file__).resolve().parent

class BuildError(ValueError):
    """Invalid inputs; no modified executable should be published."""

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def read_manifest(path: Path) -> dict[str, Any]:
    manifest = json.loads(path.read_text(encoding='utf-8-sig'))
    if site_fingerprint(manifest['patches']) != PATCH_FINGERPRINT:
        raise BuildError('Cached patch data do not match the pinned upstream patch sites.')
    if (manifest['input_sha256'], manifest['output_sha256'], manifest['file_size']) != (INPUT_HASH, OUTPUT_HASH, EXPECTED_SIZE):
        raise BuildError('Manifest identity mismatch.')
    validate_sites(manifest['patches'], EXPECTED_SIZE)
    return manifest

def validate_sites(sites: list[dict[str, Any]], size: int) -> None:
    used: set[int] = set()
    if not sites:
        raise BuildError('Empty patch table.')
    for site in sites:
        offset = int(site['offset'], 16)
        for key in ('before', 'after'):
            if not re.fullmatch(r'(?:[0-9a-fA-F]{2})+', site[key]):
                raise BuildError(f'Invalid hex at {site["offset"]}.')
        before, after = bytes.fromhex(site['before']), bytes.fromhex(site['after'])
        if len(before) != len(after):
            raise BuildError('A patch would change the file layout.')
        if offset < 0 or offset + len(before) > size:
            raise BuildError('Patch lies outside the input.')
        positions = set(range(offset, offset + len(before)))
        if used.intersection(positions):
            raise BuildError('Overlapping patch sites.')
        used.update(positions)

def pe_checksum_offset(data: bytes) -> int:
    if len(data) < 0x40 or data[:2] != b'MZ':
        raise BuildError('Not a DOS/PE executable.')
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    if pe < 0x40 or pe + 90 > len(data) or data[pe:pe+4] != b'PE\0\0':
        raise BuildError('Invalid PE header.')
    if struct.unpack_from('<H', data, pe + 4)[0] != 0x8664:
        raise BuildError('The executable is not AMD64.')
    if struct.unpack_from('<H', data, pe + 24)[0] != 0x20b:
        raise BuildError('The executable is not PE32+.')
    return pe + 88

def pe_checksum(data: bytes, offset: int) -> int:
    """Fold little-endian 16-bit words, omitting the four checksum bytes."""
    if offset < 0 or offset % 2 or offset + 4 > len(data):
        raise BuildError('Invalid PE checksum offset.')
    total = 0
    for pos in range(0, len(data), 2):
        if offset <= pos < offset + 4:
            continue
        word = data[pos] + ((data[pos+1] << 8) if pos+1 < len(data) else 0)
        total += word
        total = (total & 0xffff) + (total >> 16)
    total = (total & 0xffff) + (total >> 16)
    return (total + len(data)) & 0xffffffff

def apply_sites(data: bytes, sites: list[dict[str, Any]]) -> bytes:
    """Internal byte-operation primitive, also exercised on synthetic test data.

    This helper is NOT the public build boundary. build_bytes performs both
    exact SHA-256 checks and must be used for any real output.
    """
    validate_sites(sites, len(data))
    checksum_at = pe_checksum_offset(data)
    for site in sites:
        at = int(site['offset'], 16)
        expected = bytes.fromhex(site['before'])
        if data[at:at+len(expected)] != expected:
            raise BuildError(f'Original bytes mismatch at {site["offset"]}.')
        if at < checksum_at + 4 and at + len(expected) > checksum_at:
            raise BuildError('A patch overlaps the checksum field.')
    changed = bytearray(data)
    for site in sites:
        at = int(site['offset'], 16)
        replacement = bytes.fromhex(site['after'])
        changed[at:at+len(replacement)] = replacement
    struct.pack_into('<I', changed, checksum_at, pe_checksum(changed, checksum_at))
    return bytes(changed)

def build_bytes(data: bytes, manifest: dict[str, Any]) -> bytes:
    if len(data) != EXPECTED_SIZE:
        raise BuildError(f'Expected {EXPECTED_SIZE} bytes; got {len(data)}.')
    if digest(data) != INPUT_HASH:
        raise BuildError('Input is not the exact official WinBox 3.43 x64. No force mode exists.')
    output = apply_sites(data, manifest['patches'])
    if len(output) != EXPECTED_SIZE or digest(output) != OUTPUT_HASH:
        raise BuildError('Output hash mismatch. Nothing may be written as an EXE.')
    return output

def publish_verified(data: bytes, target: Path) -> bool:
    """Write only the pinned output, atomically, and never replace another file.

    Returns True if created, False if the exact output already exists.
    """
    if len(data) != EXPECTED_SIZE or digest(data) != OUTPUT_HASH:
        raise BuildError('Refusing to publish an unverified executable.')
    target = target.resolve()
    if target.exists():
        if target.is_file() and digest(target.read_bytes()) == OUTPUT_HASH:
            return False
        raise BuildError(f'Destination already exists and will not be overwritten: {target}')
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix='.winbox-build-', suffix='.tmp', dir=target.parent, delete=False) as stream:
        temp = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        except Exception:
            temp.unlink(missing_ok=True)
            raise
    try:
        if digest(temp.read_bytes()) != OUTPUT_HASH:
            raise BuildError('Temporary file verification failed.')
        # Creating a hard link is an atomic, no-clobber publication on NTFS/ext4.
        # Unsupported filesystems cause a safe error instead of unsafe replacement.
        os.link(temp, target)
        return True
    except FileExistsError as exc:
        raise BuildError('Destination appeared during build; it was not overwritten.') from exc
    finally:
        temp.unlink(missing_ok=True)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='Original official winbox64.exe version 3.43 x64')
    parser.add_argument('-o', '--output', type=Path, default=ROOT/'WinBox3_Compat'/'winbox64.exe')
    args = parser.parse_args(argv)
    try:
        path = ROOT/'source'/'patches.json'
        if not path.is_file():
            print('Importing hash-pinned patch metadata from the original author (text only)...')
            import_manifest(path)
        manifest = read_manifest(path)
        source, target = args.input.resolve(), args.output.resolve()
        if source == target:
            raise BuildError('Input and output must be different files.')
        result = build_bytes(source.read_bytes(), manifest)
        created = publish_verified(result, target)
        print(('Created: ' if created else 'Already verified: ') + str(target))
        print('SHA-256: ' + OUTPUT_HASH)
        print('This confirms reproducibility, NOT a router connection test.')
        print('Windows users: rerun 01_BUILD_WINBOX.cmd to copy locally cached icons.')
        return 0
    except (OSError, ValueError, KeyError) as exc:
        print('BUILD STOPPED: ' + str(exc), file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
