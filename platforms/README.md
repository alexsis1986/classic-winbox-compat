# Classic WinBox 3.43 · Linux & macOS launchers

**Source-only preview 0.1.0-preview.1 · Wine required · not a native WinBox port**

[Русский](README.ru.md) | [Linux installation](docs/LINUX_EN.md) | [macOS installation](docs/MACOS_EN.md) | [Rights & provenance](docs/RIGHTS_EN.md)

Keep the classic Windows interface; run your own locally prepared WinBox 3.43 x64 through Wine. This directory contains original launcher, installer, packaging and test sources only. It does **not** contain WinBox, Wine, fonts, MikroTik icons, upstream patch code, patch bytes or saved router sessions.

> **Experimental.** Real WinBox GUI execution and router connectivity through Wine on Linux/macOS have not been validated by this project. Unit tests use mock Wine and synthetic payloads. An earlier Windows connection reported by the maintainer is not Linux/macOS validation. This wrapper adds no new RouterOS field handlers.

## Choose your installation guide

| Platform | English | Русский |
|---|---|---|
| Linux Intel/AMD x86-64 | [Install on Linux](docs/LINUX_EN.md) | [Установка на Linux](docs/LINUX_RU.md) |
| macOS Intel; Apple Silicon via compatible Intel Wine/Rosetta | [Install on macOS](docs/MACOS_EN.md) | [Установка на macOS](docs/MACOS_RU.md) |

Linux ARM is not supported by this preview. On Apple Silicon the documented Intel Wine route depends on Rosetta; support for macOS 28 and later is not promised. Wine and its dependencies are installed separately by the user; no security settings are disabled by this project.

## Build locally, do not redistribute the resulting EXE

You need Python **3.9+** and a legally obtained, locally prepared compatible EXE. From this directory:

```bash
python3 build_packages.py --exe "/absolute/path/to/WinBox3_Compat/winbox64.exe" --out ./private-build
```

Only this exact v1.0.0-compatible patched payload is accepted:

```text
ac40890431762b588a7b7777d1ad48c54751dbfa2a3868450222dce757ec496d
```

The unmodified WinBox 3.43 input is **not** this payload. The wrapper packager does not patch, download or run an EXE. It does not obtain upstream patch data. The main repository's existing Windows patch workflow is a separate component with separate rights questions. Proceed with that component only after determining your permission or applicable legal basis; our wrapper license supplies neither.

The generated private Linux/macOS packages contain your locally supplied EXE. They are **not** the public source release. Do not upload them to GitHub without appropriate permissions.

## Public source release

```bash
python3 build_packages.py --audit-source
python3 -m unittest discover -s tests -v
python3 build_packages.py --source-only --out ./source-build
```

Public packaging uses an explicit allowlist, refuses missing files, symlinks and non-text contents, and regenerates SHA-256 checksums. `SOURCE_FILES.txt` lists the allowed source files. An unexpected file within the source tree is rejected, except for named ignored local build/cache locations. A `.gitignore` alone is not a security or copyright check.

The dedicated workflow publishes only a **pre-release** named `platforms-source-v0.1.0-preview.1`. It does not change, replace or retag the Windows release `v1.0.0`; its assets never include private builds. Existing releases are not overwritten.

## Rights and support boundary

The [MIT license](LICENSE) covers only original project-authored wrapper code and documentation. WinBox/RouterOS, Wine, Apple components and third-party patches retain their owners' rights. Public availability does not grant a redistribution license; local assembly does not automatically resolve licensing issues. See [English rights notes](docs/RIGHTS_EN.md) / [русский](docs/RIGHTS_RU.md), [NOTICE.txt](NOTICE.txt), and [validation scope](VALIDATION_REPORT.md).

This is an unofficial independent project, not endorsed by MikroTik, WineHQ, Apple or GitHub. Names identify compatibility, not affiliation. No vendor logos or screenshots are used.
