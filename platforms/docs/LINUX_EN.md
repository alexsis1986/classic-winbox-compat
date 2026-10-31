# Linux installation — Classic WinBox 3.43 via Wine

**Source-only preview 0.1.0-preview.1. Not a native Linux build.**

## 1. Requirements

Use an Intel/AMD **x86-64** Linux desktop, Python 3.9+, Bash and a trusted Wine installation capable of running 64-bit Windows programs. Linux ARM/Raspberry Pi is not supported by this kit. A headless SSH session is not enough for the GUI. No Wine runtime is bundled.

On Ubuntu 24.04 with its official repositories enabled, these are example dependency commands:

```bash
sudo apt update
sudo apt install python3 wine wine64
python3 --version
wine --version
```

For other distributions follow their maintained Wine instructions. Package names, versions and dependencies may differ. Administrator privileges are for OS package installation only: **never run WinBox, Wine or our launch/install scripts with sudo**. See the Ubuntu package links in SOURCES.md; installing Wine is not a guarantee of WinBox compatibility.

## 2. Obtain the public source and your own local payload

Download the source-only platform release and fully extract it. Alternatively clone the project and open the `platforms` directory:

```bash
git clone https://github.com/alexsis1986/classic-winbox-compat.git
cd classic-winbox-compat/platforms
```

A platform source ZIP has `build_packages.py` at its extracted root: open that directory instead of running `cd platforms` again.

Provide your locally prepared `WinBox3_Compat/winbox64.exe` from the existing Windows v1.0.0-compatible kit, only where you have the right to use that modified copy. Copy **only** the EXE to a private location; no saved sessions, router backups or credentials are needed. The official unmodified 3.43 EXE is not an accepted input to this wrapper packager. This project does not grant permission to modify or redistribute third-party code. Read the rights notes before using the separate Windows patcher.

Verify the local file:

```bash
sha256sum "$HOME/Downloads/winbox64.exe"
```

Expected **patched** SHA-256:

```text
ac40890431762b588a7b7777d1ad48c54751dbfa2a3868450222dce757ec496d
```

A digest match confirms bytes only, not security, licensing or full RouterOS support.

## 3. Build a private package

From the source directory containing `build_packages.py`:

```bash
python3 build_packages.py --audit-source
python3 build_packages.py --exe "$HOME/Downloads/winbox64.exe" --out ./private-build
```

Adjust the EXE path to your file. An existing output is not overwritten: use another `--out` directory for a repeat build. Both Linux and macOS private packages are generated; **do not upload these EXE-containing outputs to GitHub**. `--source-only` is the separate public packaging mode.

## 4. Check and launch

```bash
cd private-build/ClassicWinBox343-Linux-x86_64-preview0.1.0
bash VERIFY_FILES.sh
bash WinBox.sh --doctor
bash WinBox.sh
```

`--doctor` checks the payload hash, platform, Wine version and graphical environment. It does not launch WinBox or test any router. Normal first launch creates a dedicated 64-bit Wine prefix. Enter the router address, username and password in WinBox; the launcher refuses credential arguments.

A locally created Linux archive can instead be extracted on another compatible machine; continue from this section inside its extracted folder.

## 5. Optional desktop-menu entry

```bash
bash Install.sh
```

This performs a per-user copy into `~/.local/share/classic-winbox343/app-0.1.0-preview/` and creates `~/.local/share/applications/classic-winbox343.desktop` (or the corresponding XDG_DATA_HOME paths). Existing application directories and shortcuts are not overwritten. The installer does not install Wine or change the firewall.

For a nonstandard Wine location:

```bash
CWC_WINE_BIN=/absolute/path/to/wine bash WinBox.sh --doctor
```

For menu launches, put the absolute executable path on one line, **without quotes or arguments**, in `~/.config/classic-winbox343/wine-path.txt` (or XDG_CONFIG_HOME). Do not include a password.

## 6. Troubleshooting, data and removal

The default Wine prefix is `~/.local/share/classic-winbox343/wineprefix/`; the private last-launch log is `~/.local/share/classic-winbox343/logs/last-launch.log`. A separate prefix is **not a security sandbox**. Review and redact logs before sharing; never upload the complete prefix.

For a first test prefer a lab router or read-only account and an IP connection. Neighbors/MAC connections, advanced fields, fonts and high-DPI rendering remain unverified on Wine. The v1.0.0 field limitations remain. Do not bypass a hash error, disable antivirus or open firewall rules automatically.

No vendor icons or fonts are included. Missing icons do not prove that a RouterOS feature is supported. Optional local artwork, where permitted, must remain outside public sources.

To uninstall, remove only the `app-0.1.0-preview` directory and its `.desktop` shortcut. Keep the prefix and logs when retaining settings. No script deletes saved sessions automatically.

**Validation:** launcher tests use mock Wine; real Linux WinBox GUI and router connectivity have not been validated. Authoritative dependency sources are in [SOURCES.md](SOURCES.md).
