#!/usr/bin/env python3
"""Build private Linux/macOS Wine wrappers around an exact local WinBox payload.

The public source kit never includes any Microsoft/MikroTik binaries, artwork,
Wine runtime or machine-code patch data. Python >=3.9; standard library only.
"""
from __future__ import annotations
import argparse
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import plistlib
import shutil
import stat
import struct
import tarfile
import zipfile

ROOT = Path(__file__).resolve().parent
VERSION = '0.1.0-preview'
INPUT_SIZE = 2295976
PAYLOAD_HASH = 'ac40890431762b588a7b7777d1ad48c54751dbfa2a3868450222dce757ec496d'
LINUX_NAME = 'ClassicWinBox343-Linux-x86_64-preview0.1.0'
MAC_NAME = 'ClassicWinBox343-macOS-Wine-preview0.1.0'
SOURCE_VERSION = '0.1.0-preview.1'
SOURCE_NAME = 'ClassicWinBox343-PlatformSources-' + SOURCE_VERSION
STAMP = (2026, 10, 31, 0, 0, 0)
EPOCH = 1793404800

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def verify_payload(path: Path) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise ValueError('A regular local patched WinBox file is required; no symlinks.')
    data = path.read_bytes()
    if len(data) != INPUT_SIZE or sha(data) != PAYLOAD_HASH:
        raise ValueError('Wrong payload: only the exact v1.0.0-compatible patched EXE is accepted.')
    if data[:2] != b'MZ':
        raise ValueError('Not a DOS/PE file.')
    off = struct.unpack_from('<I', data, 0x3c)[0]
    if off + 26 > len(data) or data[off:off+4] != b'PE\0\0':
        raise ValueError('Invalid PE signature.')
    if struct.unpack_from('<H', data, off+4)[0] != 0x8664 or struct.unpack_from('<H', data, off+24)[0] != 0x20b:
        raise ValueError('Expected an AMD64 PE32+ executable.')
    return data

def copy(src: Path, dest: Path, mode: int = 0o644) -> None:
    if src.is_symlink() or not src.is_file():
        raise ValueError(f'Not a regular source file: {src}')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(src.read_bytes())
    dest.chmod(mode)

def write(path: Path, data: str | bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data.encode('utf-8') if isinstance(data,str) else data)
    path.chmod(mode)

def hash_manifest(root: Path) -> None:
    lines = []
    for p in sorted(root.rglob('*')):
        if p.is_symlink(): raise ValueError(f'Symlinks are not packaged: {p}')
        if p.is_file() and p.name != 'SHA256SUMS.txt':
            lines.append(f'{sha(p.read_bytes())}  {p.relative_to(root).as_posix()}\n')
    write(root/'SHA256SUMS.txt', ''.join(lines))

def zip_tree(root: Path, dest: Path) -> None:
    if dest.exists(): raise FileExistsError(dest)
    with zipfile.ZipFile(dest,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(root.rglob('*')):
            if p.is_symlink(): raise ValueError('Symlinks are not packaged.')
            if not p.is_file(): continue
            i=zipfile.ZipInfo(root.name+'/'+p.relative_to(root).as_posix(),STAMP)
            i.create_system=3
            i.external_attr=(stat.S_IFREG | stat.S_IMODE(p.stat().st_mode))<<16
            i.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(i,p.read_bytes(),compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
    with zipfile.ZipFile(dest) as z:
        if z.testzip(): raise RuntimeError('ZIP CRC verification failed.')

def tar_tree(root: Path,dest: Path) -> None:
    if dest.exists(): raise FileExistsError(dest)
    with dest.open('xb') as f, gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=EPOCH,compresslevel=9) as g:
        with tarfile.open(fileobj=g,mode='w',format=tarfile.PAX_FORMAT) as t:
            for p in sorted(root.rglob('*')):
                if p.is_symlink(): raise ValueError('Symlinks are not packaged.')
                if not p.is_file():continue
                data=p.read_bytes()
                i=tarfile.TarInfo(root.name+'/'+p.relative_to(root).as_posix())
                i.size=len(data);i.mode=stat.S_IMODE(p.stat().st_mode);i.mtime=EPOCH;i.uid=i.gid=0;i.uname=i.gname=''
                t.addfile(i,io.BytesIO(data))

def status(platform: str) -> dict:
    return {
        'wrapper_version': VERSION, 'date': '2026-10-31', 'target': platform,
        'winbox_client': '3.43 x64 Windows PE32+', 'binary_patch_baseline': 'v1.0.0',
        'payload_sha256': PAYLOAD_HASH, 'payload_bytes': INPUT_SIZE,
        'wine_bundled': False, 'new_routeros_field_support_added': False,
        'native_client': False, 'macos_signed_or_notarized': False,
        'wine_gui_execution_in_build_environment': 'NOT_RUN',
        'linux_router_connection': 'NOT_RUN', 'macos_router_connection': 'NOT_RUN',
        'windows_user_report': 'USER_REPORTED_CONNECTION_SUCCESS on RouterOS 7.25, hAP be3 Media (arm64), earlier Windows kit; exact EXE provenance not independently bound to screenshot',
        'publication': 'PRIVATE_LOCAL_PACKAGE; not authorized for public redistribution',
        'rights': 'No redistribution permission is asserted for MikroTik or upstream-derived payload.'
    }

def common(root: Path, platform: str) -> None:
    copy(ROOT/'docs'/f'{platform}_RU.md',root/'README_RU.md')
    copy(ROOT/'docs'/f'{platform}_EN.md',root/'README_EN.md')
    copy(ROOT/'docs'/'SOURCES.md',root/'SOURCES.md')
    copy(ROOT/'NOTICE.txt',root/'NOTICE.txt')
    copy(ROOT/'LICENSE',root/'WRAPPER_LICENSE.txt')
    if (ROOT/'VALIDATION_REPORT.md').exists():
        copy(ROOT/'VALIDATION_REPORT.md',root/'VALIDATION_REPORT.md')
    copy(ROOT/'templates'/'VERIFY_FILES.sh',root/'VERIFY_FILES.sh',0o755)
    write(root/'BUILD_STATUS.json',json.dumps(status(platform),indent=2)+'\n')

def make_packages(exe: Path, out: Path) -> list[Path]:
    data=verify_payload(exe)
    out.mkdir(parents=True,exist_ok=True)
    linux=out/LINUX_NAME; mac=out/MAC_NAME
    targets=[linux,mac,out/(LINUX_NAME+'.tar.gz'),out/(MAC_NAME+'.zip')]
    if any(p.exists() for p in targets):raise FileExistsError('Build targets already exist; use a new output directory.')
    linux.mkdir();mac.mkdir()
    common(linux,'LINUX');common(mac,'MACOS')
    copy(ROOT/'runtime'/'launch.sh',linux/'runtime'/'launch.sh',0o755)
    copy(ROOT/'templates'/'WinBox.sh',linux/'WinBox.sh',0o755)
    copy(ROOT/'templates'/'linux-install.sh',linux/'Install.sh',0o755)
    write(linux/'runtime'/'payload'/'winbox64.exe',data)
    app=mac/'Classic WinBox 3.43.app';resources=app/'Contents'/'Resources'
    copy(ROOT/'runtime'/'launch.sh',resources/'launch.sh',0o755)
    copy(ROOT/'templates'/'mac-launch',app/'Contents'/'MacOS'/'ClassicWinBox',0o755)
    copy(ROOT/'templates'/'Install.command',mac/'Install.command',0o755)
    copy(ROOT/'templates'/'01_CHECK.command',mac/'01_CHECK.command',0o755)
    write(resources/'payload'/'winbox64.exe',data)
    write(app/'Contents'/'Info.plist',plistlib.dumps({
        'CFBundleDevelopmentRegion':'en', 'CFBundleExecutable':'ClassicWinBox',
        'CFBundleIdentifier':'org.classicwinbox.compat.preview',
        'CFBundleInfoDictionaryVersion':'6.0', 'CFBundleName':'Classic WinBox 3.43',
        'CFBundleDisplayName':'Classic WinBox 3.43 (Preview)', 'CFBundlePackageType':'APPL',
        'CFBundleShortVersionString':'0.1.0','CFBundleVersion':'1',
        'LSMinimumSystemVersion':'10.15', 'NSHighResolutionCapable':True,
        'NSHumanReadableCopyright':'Unofficial Wine launcher. WinBox belongs to MikroTik. See NOTICE.txt.'
    },sort_keys=True))
    write(app/'Contents'/'PkgInfo',b'APPL????')
    copy(ROOT/'NOTICE.txt',resources/'NOTICE.txt')
    for r in (linux/'runtime'/'payload',resources/'payload'):
        write(r/'icons'/'OPTIONAL_ICONS.txt','Optional: place only your local icons.png, icons24.png and icons32.png here.\nDo not copy session databases, passwords, router exports or backups.\nNo icon artwork is included. Missing icons do not imply new GUI-type support.\n')
    hash_manifest(linux);hash_manifest(mac)
    tar_tree(linux,targets[2]);zip_tree(mac,targets[3])
    for path in targets[2:]:
        write(path.with_name(path.name+'.sha256'),f'{sha(path.read_bytes())}  {path.name}\n')
    return targets[2:]

# Explicit public-source allowlist. Adding a release file requires review here.
SOURCE_FILES = (
    '.gitattributes', '.gitignore', 'LICENSE', 'NOTICE.txt',
    'README.md', 'README.ru.md', 'RELEASE_NOTES.md', 'VALIDATION_REPORT.md',
    'SOURCE_FILES.txt', 'build_packages.py',
    'docs/COMMON_EN.md', 'docs/LINUX_EN.md', 'docs/LINUX_RU.md',
    'docs/MACOS_EN.md', 'docs/MACOS_RU.md', 'docs/RIGHTS_EN.md',
    'docs/RIGHTS_RU.md', 'docs/SOURCES.md',
    'runtime/launch.sh', 'templates/01_CHECK.command', 'templates/Install.command',
    'templates/VERIFY_FILES.sh', 'templates/WinBox.sh', 'templates/linux-install.sh',
    'templates/mac-launch', 'tests/test_platforms.py', 'tests/test_publication.py',
)
EXECUTABLE_SOURCES = {'runtime/launch.sh', 'templates/01_CHECK.command',
    'templates/Install.command', 'templates/VERIFY_FILES.sh', 'templates/WinBox.sh',
    'templates/linux-install.sh', 'templates/mac-launch'}


def audit_sources() -> tuple[str, ...]:
    """Fail on unknown source files; ignore only documented local output/cache dirs.

    This prevents accidental inclusion. It is not a legal or malware certification.
    No local EXE, patch data, Wine installation or upstream download is used.
    """
    allowed = set(SOURCE_FILES)
    if len(allowed) != len(SOURCE_FILES):
        raise ValueError('Duplicate source allowlist entry')
    for name in SOURCE_FILES:
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError('Unsafe allowlist path')
        file = ROOT / rel
        for parent in (file, *file.parents):
            if parent == ROOT.parent:
                break
            if parent.is_symlink():
                raise ValueError(f'Symlink in source path: {name}')
        if not file.is_file():
            raise ValueError(f'Missing source file: {name}')
        raw = file.read_bytes()
        if len(raw) > 1_000_000 or b'\x00' in raw:
            raise ValueError(f'Binary/oversized source content: {name}')
        raw.decode('utf-8-sig', errors='strict')
        if b'\r' in raw:
            raise ValueError(f'Source file must use LF line endings: {name}')
    listed = (ROOT/'SOURCE_FILES.txt').read_text(encoding='utf-8').splitlines()
    if listed != sorted(SOURCE_FILES):
        raise ValueError('SOURCE_FILES.txt does not match the reviewed allowlist')
    ignored_dirs = {'.git', '__pycache__', 'dist', 'wineprefix'}
    for parent, dirs, files in os.walk(ROOT, followlinks=False):
        rel_parent = Path(parent).relative_to(ROOT)
        keep = []
        for d in dirs:
            full = Path(parent)/d
            if full.is_symlink():
                raise ValueError(f'Unexpected symlink: {full.relative_to(ROOT)}')
            top_build = rel_parent == Path('.') and (d.startswith('private-build') or d.startswith('source-build'))
            if d not in ignored_dirs and not top_build:
                keep.append(d)
        dirs[:] = keep
        for name in files:
            file = Path(parent)/name
            rel = file.relative_to(ROOT).as_posix()
            if file.is_symlink():
                raise ValueError(f'Unexpected symlink: {rel}')
            if rel in allowed or rel == 'SHA256SUMS.txt' or name == '.DS_Store':
                continue
            raise ValueError(f'Unexpected public source file: {rel}')
    return SOURCE_FILES


def make_source(out: Path) -> Path:
    names = audit_sources()
    out.mkdir(parents=True, exist_ok=True)
    root = out/SOURCE_NAME
    dest = out/(SOURCE_NAME+'.zip')
    if root.exists() or dest.exists():
        raise FileExistsError('Source output exists; use a new directory')
    root.mkdir()
    for name in names:
        copy(ROOT/name, root/name, 0o755 if name in EXECUTABLE_SOURCES else 0o644)
    hash_manifest(root)
    zip_tree(root, dest)
    write(dest.with_name(dest.name+'.sha256'), f'{sha(dest.read_bytes())}  {dest.name}\n')
    return dest

def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--exe',type=Path,help='Local exact patched EXE; absent for --source-only')
    ap.add_argument('--out',type=Path,help='New output directory (required for packaging)')
    ap.add_argument('--audit-source',action='store_true',help='Audit public sources without a payload or output')
    ap.add_argument('--source-only',action='store_true')
    a=ap.parse_args()
    try:
        if a.audit_source:
            if a.exe or a.out or a.source_only: ap.error('--audit-source is used alone')
            print(f'Public source audit: PASS / {len(audit_sources())} allowed text files')
            return 0
        if not a.out: ap.error('--out is required for packaging')
        if a.source_only:
            if a.exe:ap.error('--exe must not be used with --source-only')
            print(make_source(a.out))
        else:
            if not a.exe:ap.error('--exe is required')
            for p in make_packages(a.exe,a.out):print(p)
    except (OSError,ValueError) as exc:
        ap.exit(1,f'BUILD STOPPED: {exc}\n')
    return 0
if __name__=='__main__':raise SystemExit(main())
