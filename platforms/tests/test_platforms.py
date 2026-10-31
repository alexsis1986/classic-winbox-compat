#!/usr/bin/env python3
"""No Wine/RouterOS execution: launcher mocks, packaging and optional real-byte tests."""
from __future__ import annotations
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import shlex
import stat
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest import mock
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import build_packages as b
FIXTURE=b'SYNTHETIC TEST PAYLOAD; THIS IS NOT AN EXECUTABLE\n'
FIXHASH=hashlib.sha256(FIXTURE).hexdigest()

class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='cwc wrapper test ')
        self.base=Path(self.tmp.name);self.base.chmod(0o755)
        self.home=self.base/'home with spaces';self.home.mkdir()
        self.bin=self.base/'mock binaries';self.bin.mkdir()
        self.package=self.base/'package with spaces';self.package.mkdir()
        self.runtime=self.package/'runtime';(self.runtime/'payload').mkdir(parents=True)
        self.exe=self.runtime/'payload'/'winbox64.exe';self.exe.write_bytes(FIXTURE)
        self.launch=self.runtime/'launch.sh'
        self.launch.write_text((ROOT/'runtime'/'launch.sh').read_text().replace(b.PAYLOAD_HASH,FIXHASH))
        self.trace=self.base/'run.trace';self.version_trace=self.base/'version.trace'
        self.wine=self.bin/'wine mock'
        self.wine.write_text('''#!/bin/bash
if [ "${1:-}" = --version ]; then
  printf 'version\n' >> "$CWC_VERSION_TRACE"
  [ "${CWC_VERSION_FAIL:-0}" = 0 ] || exit 42
  printf 'wine-mock-test-only\n'; exit 0
fi
printf 'argc=%s\narg1=%s\nprefix=%s\narch=%s\ndebug=%s\ncwd=%s\n' "$#" "$1" "$WINEPREFIX" "$WINEARCH" "$WINEDEBUG" "$PWD" > "$CWC_TRACE"
exit "${CWC_FAKE_EXIT:-0}"
''');self.wine.chmod(0o755)
        # A real hash utility shim for fixture files keeps Linux-script tests portable
        # on macOS runners, where the executable named sha256sum may be absent.
        # This is test-only; it neither replaces runtime hashes nor runs a real EXE.
        hashshim=self.bin/'sha256sum'
        hashcode='import hashlib,sys; p=sys.argv[1]; print(hashlib.sha256(open(p,"rb").read()).hexdigest()+"  "+p)'
        hashshim.write_text('#!/bin/bash\nexec '+shlex.quote(sys.executable)+' -c '+shlex.quote(hashcode)+' "$@"\n')
        hashshim.chmod(0o755)
        self.uname=self.bin/'uname'
        self.uname.write_text('''#!/bin/bash
case "$1" in -s) echo "${CWC_OS:-Linux}";; -m) echo "${CWC_CPU:-x86_64}";; *) exit 1;; esac
''');self.uname.chmod(0o755)
        self.env={'PATH':str(self.bin)+':/usr/bin:/bin','HOME':str(self.home),'LANG':'C.UTF-8',
                  'DISPLAY':':cwc-mock','CWC_WINE_BIN':str(self.wine),'CWC_TRACE':str(self.trace),
                  'CWC_VERSION_TRACE':str(self.version_trace)}
    def tearDown(self):self.tmp.cleanup()
    def run_shell(self,script=None,args=(),changes=None):
        env=self.env.copy()
        for k,v in (changes or {}).items():
            if v is None:env.pop(k,None)
            else:env[k]=v
        pre=None
        if hasattr(os,'geteuid') and os.geteuid()==0:
            # Run fixtures as nobody, never a real Wine runtime as root.
            for p in [self.base]+list(self.base.rglob('*')):
                if not p.is_symlink():os.chown(p,65534,65534)
            def drop():os.setgid(65534);os.setuid(65534)
            pre=drop
        return subprocess.run(['/bin/bash',str(script or self.launch),*args],env=env,
                              stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=8,preexec_fn=pre)
    @property
    def data(self):return self.home/'.local/share/classic-winbox343'
    def test_doctor_without_launch_or_data_creation(self):
        r=self.run_shell(args=['--doctor']);self.assertEqual(r.returncode,0,r.stdout)
        self.assertIn('NOT started',r.stdout);self.assertFalse(self.trace.exists());self.assertFalse(self.data.exists())
    def test_launch_one_argument_and_private_prefix(self):
        r=self.run_shell();self.assertEqual(r.returncode,0,r.stdout)
        text=self.trace.read_text();self.assertIn('argc=1\n',text);self.assertIn(str(self.exe),text)
        self.assertIn('prefix='+str(self.data/'wineprefix'),text);self.assertIn('arch=win64',text)
    def test_root_refused_before_wine(self):
        p=self.bin/'id';p.write_text('#!/bin/bash\necho 0\n');p.chmod(0o755)
        r=self.run_shell();self.assertNotEqual(r.returncode,0);self.assertIn('root',r.stdout);self.assertFalse(self.version_trace.exists())
    def test_hash_mismatch_blocks_runtime(self):
        self.exe.write_bytes(FIXTURE+b'x');r=self.run_shell();self.assertNotEqual(r.returncode,0)
        self.assertIn('SHA-256 mismatch',r.stdout);self.assertFalse(self.version_trace.exists())
    def test_missing_payload(self):
        self.exe.unlink();r=self.run_shell();self.assertNotEqual(r.returncode,0);self.assertIn('missing',r.stdout)
    def test_payload_symlink_rejected(self):
        target=self.base/'target.exe';target.write_bytes(FIXTURE);self.exe.unlink();self.exe.symlink_to(target)
        r=self.run_shell();self.assertNotEqual(r.returncode,0);self.assertIn('symlink',r.stdout)
    def test_credentials_arguments_rejected(self):
        r=self.run_shell(args=['127.0.0.1','admin','not-a-password']);self.assertNotEqual(r.returncode,0)
        self.assertIn('not accepted',r.stdout);self.assertFalse(self.trace.exists())
    def test_unknown_option_rejected(self):
        self.assertNotEqual(self.run_shell(args=['--force']).returncode,0)
    def test_linux_arm_rejected(self):
        r=self.run_shell(changes={'CWC_CPU':'aarch64'});self.assertNotEqual(r.returncode,0);self.assertIn('Unsupported platform',r.stdout)
    def test_unsupported_os(self):
        self.assertNotEqual(self.run_shell(changes={'CWC_OS':'FreeBSD'}).returncode,0)
    def test_relative_home(self):
        r=self.run_shell(changes={'HOME':'relative'});self.assertNotEqual(r.returncode,0);self.assertIn('absolute',r.stdout)
    def test_empty_home(self):
        self.assertNotEqual(self.run_shell(changes={'HOME':''}).returncode,0)
    def test_relative_wine(self):
        r=self.run_shell(changes={'CWC_WINE_BIN':'wine'});self.assertNotEqual(r.returncode,0);self.assertIn('absolute',r.stdout)
    def test_missing_wine(self):
        r=self.run_shell(changes={'CWC_WINE_BIN':'/no/such/cwc-wine'});self.assertNotEqual(r.returncode,0);self.assertIn('does not exist',r.stdout)
    def test_wine_version_failure(self):
        r=self.run_shell(changes={'CWC_VERSION_FAIL':'1'});self.assertNotEqual(r.returncode,0);self.assertFalse(self.trace.exists())
    def test_configured_wine_path(self):
        c=self.home/'.config/classic-winbox343';c.mkdir(parents=True);(c/'wine-path.txt').write_text(str(self.wine)+'\n')
        r=self.run_shell(changes={'CWC_WINE_BIN':None});self.assertEqual(r.returncode,0,r.stdout)
    def test_crlf_wine_path(self):
        c=self.home/'.config/classic-winbox343';c.mkdir(parents=True);(c/'wine-path.txt').write_bytes((str(self.wine)+'\r\n').encode())
        self.assertEqual(self.run_shell(changes={'CWC_WINE_BIN':None}).returncode,0)
    def test_empty_wine_config(self):
        c=self.home/'.config/classic-winbox343';c.mkdir(parents=True);(c/'wine-path.txt').write_text('')
        self.assertNotEqual(self.run_shell(changes={'CWC_WINE_BIN':None}).returncode,0)
    def test_no_graphical_session(self):
        r=self.run_shell(changes={'DISPLAY':None});self.assertNotEqual(r.returncode,0);self.assertIn('graphical',r.stdout);self.assertFalse(self.trace.exists())
    def test_doctor_no_graphical_session(self):
        r=self.run_shell(args=['--doctor'],changes={'DISPLAY':None});self.assertNotEqual(r.returncode,0);self.assertFalse(self.data.exists())
    def test_wayland_environment_accepted_not_certified(self):
        self.assertEqual(self.run_shell(changes={'DISPLAY':None,'WAYLAND_DISPLAY':'wayland-mock'}).returncode,0)
    def test_wine_failure_visible(self):
        r=self.run_shell(changes={'CWC_FAKE_EXIT':'7'});self.assertNotEqual(r.returncode,0);self.assertIn('code 7',r.stdout)
    def test_data_permissions_and_logs(self):
        self.assertEqual(self.run_shell().returncode,0)
        self.assertEqual(stat.S_IMODE(self.data.stat().st_mode),0o700)
        self.assertEqual(stat.S_IMODE((self.data/'logs/last-launch.log').stat().st_mode),0o600)
    def test_inherited_prefix_overridden(self):
        r=self.run_shell(changes={'WINEPREFIX':str(self.home/'.wine'),'WINEARCH':'win32'})
        self.assertEqual(r.returncode,0);self.assertIn('prefix='+str(self.data/'wineprefix'),self.trace.read_text())
        self.assertFalse((self.home/'.wine').exists())
    def test_32bit_existing_prefix_rejected_unchanged(self):
        p=self.data/'wineprefix';p.mkdir(parents=True);reg=p/'system.reg';reg.write_text('#arch=win32\n')
        r=self.run_shell();self.assertNotEqual(r.returncode,0);self.assertEqual(reg.read_text(),'#arch=win32\n');self.assertFalse(self.trace.exists())
    def test_prefix_symlink_rejected(self):
        self.data.mkdir(parents=True);(self.data/'wineprefix').symlink_to(self.home)
        self.assertNotEqual(self.run_shell().returncode,0)
    def test_data_symlink_rejected(self):
        self.data.parent.mkdir(parents=True);self.data.symlink_to(self.home)
        self.assertNotEqual(self.run_shell().returncode,0)
    def test_log_symlink_rejected(self):
        logs=self.data/'logs';logs.mkdir(parents=True);target=self.home/'dont-change';target.write_text('keep')
        (logs/'last-launch.log').symlink_to(target)
        self.assertNotEqual(self.run_shell().returncode,0);self.assertEqual(target.read_text(),'keep')
    def test_macos_x64_branch_mock(self):
        r=self.run_shell(changes={'CWC_OS':'Darwin'});self.assertEqual(r.returncode,0,r.stdout)
        self.assertIn('Library/Application Support/ClassicWinBox343/wineprefix',self.trace.read_text())
    def test_relative_xdg_data_rejected(self):
        r=self.run_shell(changes={'XDG_DATA_HOME':'relative'});self.assertNotEqual(r.returncode,0);self.assertIn('absolute',r.stdout)
    def test_payload_path_with_shell_metacharacters(self):
        new=self.base/'package $d "quotes" %u ; apostrophe\' brackets()'
        self.package.rename(new);self.package=new;self.runtime=new/'runtime';self.launch=self.runtime/'launch.sh';self.exe=self.runtime/'payload/winbox64.exe'
        r=self.run_shell();self.assertEqual(r.returncode,0,r.stdout);self.assertIn('arg1='+str(self.exe.resolve(strict=True))+'\n',self.trace.read_text())
    def setup_installer(self):
        for src,dest in [('linux-install.sh','Install.sh'),('WinBox.sh','WinBox.sh')]:
            (self.package/dest).write_text((ROOT/'templates'/src).read_text().replace(b.PAYLOAD_HASH,FIXHASH))
        (self.package/'README_RU.md').write_text('fixture README')
        return self.package/'Install.sh'
    def test_install_and_launch_installed_copy(self):
        r=self.run_shell(self.setup_installer());self.assertEqual(r.returncode,0,r.stdout)
        exe=self.data/'app-0.1.0-preview/WinBox.sh'
        r=self.run_shell(exe);self.assertEqual(r.returncode,0,r.stdout)
        shortcut=self.home/'.local/share/applications/classic-winbox343.desktop'
        self.assertIn('Exec=/bin/bash "',shortcut.read_text())
    def test_installer_no_existing_overwrite(self):
        p=self.setup_installer();self.assertEqual(self.run_shell(p).returncode,0)
        r=self.run_shell(p);self.assertNotEqual(r.returncode,0);self.assertIn('Already exists',r.stdout)
    def test_installer_rejects_corrupt_payload(self):
        p=self.setup_installer();self.exe.write_bytes(b'bad');r=self.run_shell(p)
        self.assertNotEqual(r.returncode,0);self.assertFalse((self.data/'app-0.1.0-preview').exists())
    def test_installer_rejects_non_linux(self):
        self.assertNotEqual(self.run_shell(self.setup_installer(),changes={'CWC_OS':'Darwin'}).returncode,0)
    def test_installer_rejects_control_character_in_path(self):
        r=self.run_shell(self.setup_installer(),changes={'XDG_DATA_HOME':str(self.home/'break\nline')})
        self.assertNotEqual(r.returncode,0);self.assertIn('Control characters',r.stdout)
    def test_desktop_escapes_metacharacters(self):
        d=str(self.home/'data "$d`x`%u\\')
        r=self.run_shell(self.setup_installer(),changes={'XDG_DATA_HOME':d});self.assertEqual(r.returncode,0,r.stdout)
        text=(Path(d)/'applications/classic-winbox343.desktop').read_text()
        self.assertIn('%%u',text);self.assertIn('\\\\$',text);self.assertIn('\\\\`',text);self.assertIn('\\\\\\\\',text)

class SourceTests(unittest.TestCase):
    def test_all_shells_parse(self):
        for p in [ROOT/'runtime/launch.sh',*list((ROOT/'templates').iterdir())]:
            with self.subTest(path=p.name):
                r=subprocess.run(['/bin/bash','-n',str(p)],capture_output=True,text=True)
                self.assertEqual(r.returncode,0,r.stderr)
    def test_source_zip_excludes_executables_and_patches(self):
        with tempfile.TemporaryDirectory() as t:
            out=b.make_source(Path(t))
            with zipfile.ZipFile(out) as z:
                self.assertIsNone(z.testzip());names=z.namelist()
                self.assertFalse(any(Path(n).suffix.lower() in ('.exe','.dll','.png','.npk') for n in names))
                self.assertFalse(any(n.endswith('patches.json') for n in names))
                self.assertTrue(any(n.endswith('runtime/launch.sh') for n in names))
    def test_source_zip_reproducible(self):
        with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as c:
            self.assertEqual(b.make_source(Path(a)).read_bytes(),b.make_source(Path(c)).read_bytes())
    def test_bad_payload_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'bad.exe';p.write_bytes(FIXTURE)
            with self.assertRaises(ValueError):b.verify_payload(p)
    def test_missing_payload_rejected(self):
        with self.assertRaises(ValueError):b.verify_payload(Path('/no/cwc/file.exe'))
    def test_no_automatic_security_bypass(self):
        for p in [ROOT/'runtime/launch.sh',*list((ROOT/'templates').iterdir())]:
            lines='\n'.join(x for x in p.read_text().splitlines() if not x.lstrip().startswith('#'))
            for prohibited in ('spctl --master-disable','xattr -d','xattr -cr','sudo wine','curl |','wget |','eval '):
                self.assertNotIn(prohibited,lines)
    def test_runtime_has_no_download(self):
        lines='\n'.join(x for x in (ROOT/'runtime/launch.sh').read_text().splitlines() if not x.lstrip().startswith('#'))
        self.assertNotRegex(lines,r'\b(curl|wget|brew|apt-get)\b')
    def test_baseline_hash_exact(self):
        self.assertIn(b.PAYLOAD_HASH,(ROOT/'runtime/launch.sh').read_text())
    def test_templates_do_not_contain_crlf(self):
        for p in [ROOT/'runtime/launch.sh',*list((ROOT/'templates').iterdir())]:self.assertNotIn(b'\r\n',p.read_bytes())
    def test_source_builder_no_network(self):
        src=(ROOT/'build_packages.py').read_text();self.assertNotIn('urlopen(',src);self.assertNotIn('requests.get(',src)

@unittest.skipUnless(os.environ.get('CWC_TEST_EXE'),'CWC_TEST_EXE absent; no proprietary fixture in public source')
class RealPayloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.exe=Path(os.environ['CWC_TEST_EXE'])
        cls.temp=tempfile.TemporaryDirectory();cls.out=Path(cls.temp.name)
        cls.archives=b.make_packages(cls.exe,cls.out)
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def test_exact_real_payload(self):self.assertEqual(b.sha(b.verify_payload(self.exe)),b.PAYLOAD_HASH)
    def test_linux_tar_hashes_and_no_links(self):
        with tarfile.open(self.archives[0]) as t:
            names=t.getnames();self.assertFalse(any(p.issym() or p.islnk() for p in t.getmembers()))
            manifest=t.extractfile(b.LINUX_NAME+'/SHA256SUMS.txt').read().decode()
            for line in manifest.splitlines():
                digest,rel=line.split('  ',1);self.assertEqual(b.sha(t.extractfile(b.LINUX_NAME+'/'+rel).read()),digest)
            self.assertEqual(t.getmember(b.LINUX_NAME+'/WinBox.sh').mode,0o755)
    def test_mac_zip_manifest(self):
        with zipfile.ZipFile(self.archives[1]) as z:
            self.assertIsNone(z.testzip())
            for line in z.read(b.MAC_NAME+'/SHA256SUMS.txt').decode().splitlines():
                digest,rel=line.split('  ',1);self.assertEqual(b.sha(z.read(b.MAC_NAME+'/'+rel)),digest)
    def test_mac_plist_and_executable_mode(self):
        with zipfile.ZipFile(self.archives[1]) as z:
            prefix=b.MAC_NAME+'/Classic WinBox 3.43.app/Contents/'
            info=plistlib.loads(z.read(prefix+'Info.plist'));self.assertEqual(info['CFBundleExecutable'],'ClassicWinBox')
            self.assertEqual(info['CFBundlePackageType'],'APPL')
            self.assertEqual((z.getinfo(prefix+'MacOS/ClassicWinBox').external_attr>>16)&0o777,0o755)
    def test_two_packages_same_binary(self):
        with tarfile.open(self.archives[0]) as t,zipfile.ZipFile(self.archives[1]) as z:
            a=t.extractfile(b.LINUX_NAME+'/runtime/payload/winbox64.exe').read()
            c=z.read(b.MAC_NAME+'/Classic WinBox 3.43.app/Contents/Resources/payload/winbox64.exe')
            self.assertEqual(a,c);self.assertEqual(b.sha(a),b.PAYLOAD_HASH)
    def test_private_packages_have_no_real_credentials(self):
        with zipfile.ZipFile(self.archives[1]) as z:
            self.assertFalse(any(Path(n).name.lower() in ('settings.cfg','addresses.cdb','session.wbx') for n in z.namelist()))
    def test_repeated_build_refuses_overwrite(self):
        with self.assertRaises(FileExistsError):b.make_packages(self.exe,self.out)
    def test_archives_reproducible(self):
        with tempfile.TemporaryDirectory() as t:
            new=b.make_packages(self.exe,Path(t))
            for old,p in zip(self.archives,new):self.assertEqual(old.read_bytes(),p.read_bytes())

if __name__=='__main__':unittest.main(verbosity=2)
