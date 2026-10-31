# macOS installation — Classic WinBox 3.43 via Wine

**Source-only preview 0.1.0-preview.1. Not a native Universal/ARM client.**

## 1. Requirements and Wine

Use Python 3.9+ and a trusted macOS Wine build supporting Windows x64, installed with all of that build's dependencies. The actual minimum macOS version is determined by the chosen Wine runtime; this project's app metadata is not a compatibility certification.

For Intel Macs use compatible x86-64 Wine. On Apple Silicon the documented Intel Wine route additionally needs Rosetta 2; use Apple's normal installation prompt if needed. Our scripts neither install Rosetta nor accept license terms for you. Apple limits general Rosetta availability to macOS 27 and earlier; no support for macOS 28+ is promised.

The Wine build maintainer provides manual download/install instructions:

- https://github.com/Gcenx/macOS_Wine_builds
- https://github.com/Gcenx/macOS_Wine_builds/releases

Read the exact release's OS and runtime dependency requirements. Copying Wine alone may not install required frameworks. Homebrew's `wine-stable` cask is listed as **disabled** as checked on 2026-10-31; do not rely on the outdated `brew install --cask wine-stable` shortcut or bypass OS security checks to force it.

Wine is not bundled or modified. Stop on malware warnings. Do not disable Gatekeeper or remove quarantine recursively. See Apple and Homebrew primary links in SOURCES.md.

## 2. Source and local compatible EXE

Extract the public source-only platform ZIP and open the directory containing `build_packages.py`. Alternatively:

```bash
git clone https://github.com/alexsis1986/classic-winbox-compat.git
cd classic-winbox-compat/platforms
python3 --version
```

Supply your own legally obtained and locally prepared `WinBox3_Compat/winbox64.exe` matching the existing Windows v1.0.0-compatible kit. Transfer only that EXE, not sessions or passwords. The unmodified vendor EXE is not an accepted wrapper input. The wrapper does not grant rights to modify or distribute third-party software; the Windows patcher is separate and has unresolved permission considerations described in the project notices.

```bash
shasum -a 256 "$HOME/Downloads/winbox64.exe"
```

Required patched-file SHA-256:

```text
ac40890431762b588a7b7777d1ad48c54751dbfa2a3868450222dce757ec496d
```

## 3. Create your private app locally

```bash
python3 build_packages.py --audit-source
python3 build_packages.py --exe "$HOME/Downloads/winbox64.exe" --out ./private-build
cd private-build/ClassicWinBox343-macOS-Wine-preview0.1.0
bash VERIFY_FILES.sh
bash 01_CHECK.command
```

Adjust the local EXE path as needed. Build outputs are not overwritten. Both platforms' private archives are generated. These outputs contain your EXE: **do not upload them to GitHub without the necessary rights**. The public source release is built separately using `--source-only`.

`01_CHECK.command` checks the app in the current extracted/build directory, not an older copy in Applications. It does not start WinBox or test a router. For a package you already built locally and transferred to this Mac, extract it with Archive Utility, open its folder in Terminal, and start with the last two commands above.

## 4. Install and open

```bash
bash Install.command
open "$HOME/Applications/Classic WinBox 3.43.app"
```

The installer copies the complete bundle to `~/Applications`, restores launcher executable bits and refuses to overwrite an existing app. It does not need sudo. Alternatively drag the full `.app` into your user Applications folder. Do not copy individual files out of `Contents`.

The app is **not Developer-ID signed or notarized**. The modified Windows file also no longer validates against its original vendor Authenticode signature. Checksums are not a malware or signing certificate. macOS may block the app; read Apple's normal app-safety guidance and decide only after verifying the source. No Gatekeeper/quarantine changes are performed by these scripts. Do not proceed on a malware or damaged-file warning.

## 5. Nonstandard Wine installation

The launcher checks PATH, common Wine bundles in `/Applications` and `~/Applications`, and common Homebrew/MacPorts locations. For explicit diagnostics:

```bash
CWC_WINE_BIN="/absolute/path/to/wine" bash 01_CHECK.command
```

For Finder launches, create `~/Library/Application Support/ClassicWinBox343/wine-path.txt` and place the absolute Wine executable path on a single line, without quotes or arguments. A path to a runtime's correct launcher may be required to load its dependencies. Do not put credentials here.

## 6. Data, limitations and removal

Wine prefix: `~/Library/Application Support/ClassicWinBox343/wineprefix/`.
Private last-launch log: `~/Library/Application Support/ClassicWinBox343/logs/last-launch.log`.

The dedicated prefix is not a security sandbox. Keep saved sessions private and redact logs. Router address and credentials are entered only inside WinBox. Prefer a lab/read-only account and IP connection for initial tests; Neighbors/MAC connections, GUI rendering and all RouterOS operations remain unverified on macOS. No vendor icons or fonts are bundled. The wrapper adds no new RouterOS handlers.

To uninstall, remove the app from `~/Applications`. Keep the prefix when retaining sessions; no automatic data deletion is performed.

**Validation:** package structure and shell behavior are tested with mock Wine; real macOS, Rosetta, Gatekeeper, Wine GUI and router operations are not certified. Dependency sources: [SOURCES.md](SOURCES.md).
