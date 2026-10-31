"""Synthetic-data tests. Import pinned upstream metadata before running them.

Run: python scripts/import_upstream.py && python -m unittest discover -s tests -v
The tests do not establish Windows execution or RouterOS compatibility.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import build_winbox as b

M = json.loads((ROOT/'source'/'patches.json').read_text())

def fixture() -> bytes:
    buf = bytearray(b.EXPECTED_SIZE)
    buf[:2] = b'MZ'
    struct.pack_into('<I', buf, 0x3c, 0x80)
    buf[0x80:0x84] = b'PE\0\0'
    struct.pack_into('<H', buf, 0x84, 0x8664)
    struct.pack_into('<H', buf, 0x86, 1)
    struct.pack_into('<H', buf, 0x94, 0xf0)
    struct.pack_into('<H', buf, 0x98, 0x20b)
    buf[0x188:0x190] = b'.text\0\0\0'
    struct.pack_into('<I', buf, 0x190, 0x130468)
    struct.pack_into('<I', buf, 0x194, 0x1000)
    struct.pack_into('<I', buf, 0x198, 0x130600)
    struct.pack_into('<I', buf, 0x19c, 0x400)
    for s in M['patches']:
        offset = int(s['offset'], 16)
        raw = bytes.fromhex(s['before'])
        buf[offset:offset+len(raw)] = raw
    return bytes(buf)

# Independent checksum expression: sum all words, then fold the entire total.
def reference_checksum(data: bytes, offset: int) -> int:
    work = bytearray(data)
    work[offset:offset+4] = b'\0' * 4
    if len(work) % 2:
        work.append(0)
    value = sum(w[0] for w in struct.iter_unpack('<H', work))
    while value >> 16:
        value = (value & 0xffff) + (value >> 16)
    return (value + len(data)) & 0xffffffff

class ImportTests(unittest.TestCase):
    def test_pinned_patch_metadata_matches_importer(self):
        from scripts import import_upstream as upstream
        self.assertEqual(upstream.site_fingerprint(M['patches']), upstream.PATCH_FINGERPRINT)
        self.assertEqual(upstream.UPSTREAM_COMMIT,M['upstream_commit'])
    def test_git_blob_hash_has_content_length(self):
        from scripts import import_upstream as upstream
        raw=b'hello'
        self.assertEqual(upstream.git_blob_sha1(raw), hashlib.sha1(b'blob 5\0hello').hexdigest())
    def test_parse_site_table_from_pinned_data_without_code_execution(self):
        from scripts import import_upstream as upstream
        import unittest.mock as mock
        groups={}
        for site in M['patches']:
            groups.setdefault(site['id'],[]).append(site)
        raw=''.join("Patch('%s', 'test', '', [%s]),\n" % (group, ','.join("(%s, %s, '%s', '%s')"%(site['offset'],site['va'] or 'None',site['before'],site['after']) for site in members)) for group,members in groups.items()).encode('utf-8')
        with mock.patch.object(upstream,'UPSTREAM_BLOB_SHA1',upstream.git_blob_sha1(raw)):
            parsed=upstream.parse_upstream(raw)
        self.assertEqual(upstream.site_fingerprint(parsed['patches']), upstream.site_fingerprint(M['patches']))
        self.assertEqual([s['id'] for s in parsed['patches']], [s['id'] for s in M['patches']])
    def test_bad_upstream_blob_rejected(self):
        from scripts import import_upstream as upstream
        with self.assertRaises(ValueError): upstream.parse_upstream(b'not pinned upstream bytes')

class ManifestTests(unittest.TestCase):
    def test_pinned_manifest_hash(self):
        self.assertEqual(b.site_fingerprint(M['patches']), b.PATCH_FINGERPRINT)
    def test_manifest_load(self):
        self.assertEqual(b.read_manifest(ROOT/'source'/'patches.json')['file_size'], b.EXPECTED_SIZE)
    def test_twenty_sites_and_twelve_groups(self):
        self.assertEqual(len(M['patches']), 20)
        self.assertEqual(len({s['id'] for s in M['patches']}), 12)
    def test_commit_is_pinned(self):
        self.assertEqual(M['upstream_commit'], 'b22d97ee6fb222e14ff35151634bdac42a9f5d29')
    def test_manifest_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'patches.json'
            fake=copy.deepcopy(M);fake['patches'][0]['after']='00'
            p.write_text(json.dumps(fake))
            with self.assertRaises(b.BuildError): b.read_manifest(p)
    def test_sites_fit_without_overlap(self):
        b.validate_sites(M['patches'], b.EXPECTED_SIZE)
    def test_empty_table_rejected(self):
        with self.assertRaises(b.BuildError): b.validate_sites([], b.EXPECTED_SIZE)
    def test_unequal_lengths_rejected(self):
        s = copy.deepcopy(M['patches'])
        s[0]['after'] += '00'
        with self.assertRaises(b.BuildError): b.validate_sites(s, b.EXPECTED_SIZE)
    def test_overlap_rejected(self):
        with self.assertRaises(b.BuildError): b.validate_sites(M['patches']+[M['patches'][0]], b.EXPECTED_SIZE)
    def test_out_of_bounds_rejected(self):
        s = copy.deepcopy(M['patches'])
        s[0]['offset'] = hex(b.EXPECTED_SIZE)
        with self.assertRaises(b.BuildError): b.validate_sites(s, b.EXPECTED_SIZE)
    def test_negative_offset_rejected(self):
        s = copy.deepcopy(M['patches'])
        s[0]['offset'] = '-1'
        with self.assertRaises(b.BuildError): b.validate_sites(s, b.EXPECTED_SIZE)
    def test_invalid_hex_rejected(self):
        s = copy.deepcopy(M['patches'])
        s[0]['after'] = 'zz'
        with self.assertRaises(b.BuildError): b.validate_sites(s, b.EXPECTED_SIZE)
    def test_odd_hex_rejected(self):
        s = copy.deepcopy(M['patches'])
        s[0]['before'] = '0'
        with self.assertRaises(b.BuildError): b.validate_sites(s, b.EXPECTED_SIZE)
    def test_code_caves_fit_extended_text(self):
        for s in M['patches']:
            at = int(s['offset'],16)
            if at >= 0x130870:
                self.assertLessEqual(at+len(bytes.fromhex(s['after'])), 0x130a00)
                self.assertEqual(set(bytes.fromhex(s['before'])), {0})
    def test_file_to_va_mapping(self):
        for s in M['patches']:
            if s['va']:
                self.assertEqual(int(s['va'],16)-int(s['offset'],16), 0x400c00)
    def test_hooks_target_expected_caves(self):
        expected={0xa6d3e:0x5314f0,0xa2b96:0x531491,0x83c62:0x5314d2,0xdcabe:0x531518}
        for s in M['patches']:
            at=int(s['offset'],16)
            if at in expected:
                raw=bytes.fromhex(s['after'])
                self.assertEqual(raw[0],0xe9)
                target=int(s['va'],16)+5+struct.unpack('<i',raw[1:5])[0]
                self.assertEqual(target,expected[at])
    def test_four_byte_hook_retains_fifth_zero(self):
        s=next(s for s in M['patches'] if s['offset']=='0x0a0826')
        raw=bytes.fromhex(s['after'])+b'\0'
        self.assertEqual(0x4a1426+5+struct.unpack('<i',raw[1:])[0],0x5314b0)

class ByteEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=fixture()
        cls.result=b.apply_sites(cls.data,M['patches'])
    def test_fixture_is_not_real_winbox(self):
        self.assertNotEqual(b.digest(self.data),b.INPUT_HASH)
        self.assertNotEqual(b.digest(self.result),b.OUTPUT_HASH)
    def test_length_preserved(self):
        self.assertEqual(len(self.result),len(self.data))
    def test_all_replacements_exact(self):
        for s in M['patches']:
            at=int(s['offset'],16); value=bytes.fromhex(s['after'])
            self.assertEqual(self.result[at:at+len(value)],value,s['id'])
    def test_no_other_bytes_changed(self):
        allowed=set(range(0xd8,0xdc))
        for s in M['patches']:
            at=int(s['offset'],16)
            allowed.update(range(at,at+len(bytes.fromhex(s['after']))))
        bad=[i for i,(old,new) in enumerate(zip(self.data,self.result)) if old!=new and i not in allowed]
        self.assertEqual(bad,[])
    def test_checksum_matches_independent_calculation(self):
        actual=struct.unpack_from('<I',self.result,0xd8)[0]
        self.assertEqual(actual,reference_checksum(self.result,0xd8))
    def test_original_preserved(self):
        self.assertEqual(self.data,fixture())
    def test_damaged_site_rejected(self):
        damaged=bytearray(self.data); damaged[0xf991c]^=1
        with self.assertRaises(b.BuildError): b.apply_sites(bytes(damaged),M['patches'])
    def test_double_patch_rejected(self):
        with self.assertRaises(b.BuildError): b.apply_sites(self.result,M['patches'])
    def test_production_boundary_rejects_synthetic(self):
        with self.assertRaises(b.BuildError): b.build_bytes(self.data,M)
    def test_input_size_mismatch(self):
        with self.assertRaises(b.BuildError): b.build_bytes(b'MZ',M)
    def test_output_hash_mismatch_is_rejected(self):
        # Permit ONLY this synthetic input hash for this test. Output remains pinned.
        with patch.object(b,'INPUT_HASH',b.digest(self.data)):
            with self.assertRaises(b.BuildError): b.build_bytes(self.data,M)
    def test_full_pipeline_on_test_only_hashes(self):
        with patch.object(b,'INPUT_HASH',b.digest(self.data)),patch.object(b,'OUTPUT_HASH',b.digest(self.result)):
            self.assertEqual(b.build_bytes(self.data,M),self.result)
    def test_checksum_field_omitted(self):
        changed=bytearray(self.data); changed[0xd8:0xdc]=b'\xff\xff\xff\xff'
        self.assertEqual(b.pe_checksum(changed,0xd8),b.pe_checksum(self.data,0xd8))
    def test_checksum_odd_lengths_and_carries(self):
        rng=random.Random(725)
        for size in (4,5,6,65,256,1025,65537):
            raw=bytes(rng.randrange(256) for _ in range(size))
            self.assertEqual(b.pe_checksum(raw,0),reference_checksum(raw,0))
        raw=b'\xff'*100001
        self.assertEqual(b.pe_checksum(raw,2),reference_checksum(raw,2))
    def test_checksum_bad_offset(self):
        for offset in (-1,1,1000):
            with self.assertRaises(b.BuildError): b.pe_checksum(b'\0'*100,offset)
    def test_bad_dos_header(self):
        with self.assertRaises(b.BuildError): b.pe_checksum_offset(b'\0'*100)
    def test_bad_pe_signature(self):
        data=bytearray(self.data); data[0x80]=0
        with self.assertRaises(b.BuildError): b.pe_checksum_offset(data)
    def test_bad_pe_offset(self):
        data=bytearray(self.data); struct.pack_into('<I',data,0x3c,0xffffffff)
        with self.assertRaises(b.BuildError): b.pe_checksum_offset(data)
    def test_32bit_pe_rejected(self):
        data=bytearray(self.data); struct.pack_into('<H',data,0x84,0x14c)
        with self.assertRaises(b.BuildError): b.pe_checksum_offset(data)
    def test_wrong_optional_header(self):
        data=bytearray(self.data); struct.pack_into('<H',data,0x98,0x10b)
        with self.assertRaises(b.BuildError): b.pe_checksum_offset(data)
    def test_checksum_overlap_rejected(self):
        sites=[dict(id='test',offset='0xd8',before='0000',after='0100')]
        with self.assertRaises(b.BuildError): b.apply_sites(self.data,sites)

class FileSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result=b.apply_sites(fixture(),M['patches'])
    def test_unverified_bytes_never_published(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'no.exe'
            with self.assertRaises(b.BuildError): b.publish_verified(self.result,target)
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(td).iterdir()),[])
    def test_atomic_publish_under_test_hash_only(self):
        with tempfile.TemporaryDirectory() as td,patch.object(b,'OUTPUT_HASH',b.digest(self.result)):
            target=Path(td)/'new.exe'
            self.assertTrue(b.publish_verified(self.result,target))
            self.assertEqual(target.read_bytes(),self.result)
            self.assertEqual(sorted(p.name for p in Path(td).iterdir()),['new.exe'])
    def test_identical_existing_file_retained(self):
        with tempfile.TemporaryDirectory() as td,patch.object(b,'OUTPUT_HASH',b.digest(self.result)):
            target=Path(td)/'new.exe'; target.write_bytes(self.result)
            self.assertFalse(b.publish_verified(self.result,target))
    def test_existing_different_file_never_overwritten(self):
        with tempfile.TemporaryDirectory() as td,patch.object(b,'OUTPUT_HASH',b.digest(self.result)):
            target=Path(td)/'keep.exe'; target.write_bytes(b'keep-me')
            with self.assertRaises(b.BuildError): b.publish_verified(self.result,target)
            self.assertEqual(target.read_bytes(),b'keep-me')
    def test_same_input_output_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            target=Path(td)/'source.exe'; target.write_bytes(b'keep-me')
            self.assertEqual(b.main([str(target),'-o',str(target)]),1)
            self.assertEqual(target.read_bytes(),b'keep-me')
    def test_invalid_cli_input_does_not_create_output(self):
        with tempfile.TemporaryDirectory() as td:
            original=Path(td)/'original.exe'; original.write_bytes(b'MZ-not-real')
            out=Path(td)/'out.exe'
            r=subprocess.run([sys.executable,str(ROOT/'build_winbox.py'),str(original),'-o',str(out)],capture_output=True,text=True)
            self.assertEqual(r.returncode,1)
            self.assertFalse(out.exists())
            self.assertEqual(original.read_bytes(),b'MZ-not-real')
    def test_no_force_argument(self):
        r=subprocess.run([sys.executable,str(ROOT/'build_winbox.py'),'--force'],capture_output=True,text=True)
        self.assertNotEqual(r.returncode,0)

class WindowsStaticTests(unittest.TestCase):
    """Text checks only. These are NOT a PowerShell parser or Windows runtime."""
    @classmethod
    def setUpClass(cls):
        cls.ps=(ROOT/'WinBox-Toolkit.ps1').read_text(encoding='utf-8-sig')
    def test_windows_manifest_hash_matches(self):
        self.assertIn("$PatchFingerprint = '"+b.PATCH_FINGERPRINT+"'",self.ps)
    def test_windows_input_hash_matches(self):
        self.assertIn("$InputHash = '"+b.INPUT_HASH+"'",self.ps)
    def test_windows_output_hash_matches(self):
        self.assertIn("$OutputHash = '"+b.OUTPUT_HASH+"'",self.ps)
    def test_download_is_official_https_only(self):
        self.assertIn("$SourceUrl = 'https://download.mikrotik.com/routeros/winbox/3.43/winbox64.exe'",self.ps)
        self.assertIn('-MaximumRedirection 0',self.ps)
        self.assertNotIn('http://',self.ps)
    def test_block_comment_is_closed(self):
        self.assertEqual(self.ps.count('<#'),1)
        self.assertEqual(self.ps.count('#>'),1)
        self.assertLess(self.ps.index('#>'),self.ps.index('[CmdletBinding()]'))
    def test_not_weakening_windows_security(self):
        for forbidden in ('Set-MpPreference','Add-MpPreference','Set-ExecutionPolicy','Unblock-File','ServerCertificateValidationCallback','-Verb RunAs','Invoke-Expression'):
            self.assertNotIn(forbidden,self.ps)
    def test_launchers_have_windows_line_endings(self):
        for name in ('01_BUILD_WINBOX.cmd','02_RUN_WINBOX.cmd','03_VERIFY_FILES.cmd'):
            raw=(ROOT/name).read_bytes()
            self.assertNotIn(b'\n',raw.replace(b'\r\n',b''))
    def test_build_launcher_does_not_run_exe(self):
        text=(ROOT/'01_BUILD_WINBOX.cmd').read_text()
        self.assertIn('-Mode Build',text)
        self.assertNotIn('-Mode Run',text)
    def test_launch_is_guarded_by_expected_hash(self):
        needle="if ((Hash-File $OutputExe) -ne $OutputHash) { throw 'EXE hash differs"
        self.assertIn(needle,self.ps)
        self.assertLess(self.ps.index(needle),self.ps.index('Start-Process -FilePath $OutputExe'))
    def test_no_unfilled_placeholders(self):
        self.assertNotIn('__MANIFEST_HASH__',self.ps)
        self.assertNotIn('__MANIFEST_HASH__',(ROOT/'build_winbox.py').read_text())

if __name__=='__main__':
    unittest.main(verbosity=2)
