"""Publication guards; synthetic data only, no network or proprietary payload."""
from pathlib import Path
import hashlib
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import build_packages as b

class PublicationTests(unittest.TestCase):
    def fixture(self, root):
        for name in b.SOURCE_FILES:
            dst=root/name;dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/name,dst)
    def test_allowlist_matches_manifest(self):
        self.assertEqual((ROOT/'SOURCE_FILES.txt').read_text().splitlines(), sorted(b.SOURCE_FILES))
    def test_public_source_audit(self):
        self.assertEqual(set(b.audit_sources()),set(b.SOURCE_FILES))
    def test_all_four_install_guides_present(self):
        for name in ('LINUX_EN.md','LINUX_RU.md','MACOS_EN.md','MACOS_RU.md'):
            self.assertIn('docs/'+name,b.SOURCE_FILES)
            text=(ROOT/'docs'/name).read_text()
            self.assertIn('build_packages.py',text)
            self.assertIn('ac408904',text)
    def test_both_rights_guides_present(self):
        for lang in ('EN','RU'):
            self.assertIn('docs/RIGHTS_'+lang+'.md',b.SOURCE_FILES)
    def test_zip_exact_allowlist_and_generated_checksums(self):
        with tempfile.TemporaryDirectory() as t:
            archive=b.make_source(Path(t))
            with zipfile.ZipFile(archive) as z:
                names={n.split('/',1)[1] for n in z.namelist()}
                self.assertEqual(names,set(b.SOURCE_FILES)|{'SHA256SUMS.txt'})
                for line in z.read(b.SOURCE_NAME+'/SHA256SUMS.txt').decode().splitlines():
                    digest,name=line.split('  ',1)
                    self.assertEqual(hashlib.sha256(z.read(b.SOURCE_NAME+'/'+name)).hexdigest(),digest)
    def test_unknown_session_file_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);(root/'saved-sessions.txt').write_text('private fixture')
            with patch.object(b,'ROOT',root),self.assertRaisesRegex(ValueError,'Unexpected'):
                b.audit_sources()
    def test_binary_disguised_as_document_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);(root/'docs/COMMON_EN.md').write_bytes(b'MZ\0fixture')
            with patch.object(b,'ROOT',root),self.assertRaisesRegex(ValueError,'Binary'):
                b.audit_sources()
    def test_invalid_utf8_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);(root/'docs/COMMON_EN.md').write_bytes(b'\xff\xfe')
            with patch.object(b,'ROOT',root),self.assertRaises(UnicodeError):
                b.audit_sources()
    def test_missing_source_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);(root/'README.ru.md').unlink()
            with patch.object(b,'ROOT',root),self.assertRaisesRegex(ValueError,'Missing'):
                b.audit_sources()
    def test_crlf_source_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);(root/'runtime/launch.sh').write_bytes(b'#!/bin/bash\r\n')
            with patch.object(b,'ROOT',root),self.assertRaisesRegex(ValueError,'LF'):
                b.audit_sources()
    def test_symlink_source_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);f=root/'README.ru.md';f.unlink();f.symlink_to(root/'README.md')
            with patch.object(b,'ROOT',root),self.assertRaisesRegex(ValueError,'Symlink'):
                b.audit_sources()
    def test_local_payload_in_ignored_build_never_packaged(self):
        with tempfile.TemporaryDirectory() as t,tempfile.TemporaryDirectory() as o:
            root=Path(t);self.fixture(root);d=root/'private-build';d.mkdir();(d/'winbox64.exe').write_bytes(b'MZ\0fixture')
            with patch.object(b,'ROOT',root):
                zpath=b.make_source(Path(o))
                with zipfile.ZipFile(zpath) as z:
                    self.assertFalse(any(n.endswith('.exe') or 'private-build' in n for n in z.namelist()))
    def test_patches_outside_build_are_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root);(root/'patches.json').write_text('{}')
            with patch.object(b,'ROOT',root),self.assertRaisesRegex(ValueError,'Unexpected'):
                b.audit_sources()
    def test_no_metadata_can_silently_extend_allowlist(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);self.fixture(root)
            with (root/'SOURCE_FILES.txt').open('a') as f:f.write('extra.txt\n')
            with patch.object(b,'ROOT',root),self.assertRaisesRegex(ValueError,'allowlist'):
                b.audit_sources()
    def test_source_refuses_existing_output(self):
        with tempfile.TemporaryDirectory() as t:
            b.make_source(Path(t))
            with self.assertRaises(FileExistsError):b.make_source(Path(t))

if __name__=='__main__':unittest.main()
