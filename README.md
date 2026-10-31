# Classic WinBox Compatibility

**An unofficial, community-oriented compatibility toolkit for MikroTik WinBox 3.43 x64 on RouterOS 7.25.**

[🇷🇺 Русская версия](README.ru.md) · [Compatibility matrix](docs/COMPATIBILITY.md) · [Security](SECURITY.md) · [Credits / legal](docs/LEGAL.md) · [Changelog](CHANGELOG.md)

> [!IMPORTANT]
> This project is **not affiliated with or endorsed by MikroTik**. This is a **local binary patcher**, **not a new WinBox client**, and it **does not distribute WinBox executables or MikroTik artwork**. If you need a supported administration tool, use the official WinBox 4.

## Why this exists

RouterOS 7.25 requires WinBox 4.3 or newer. Many administrators still prefer the classic WinBox 3 interface. This toolkit preserves that familiar workflow, where technically possible, by applying a **specific, hash-verified compatibility patch** to an official, locally obtained copy of WinBox 3.43 x64.

The patch skips unsupported interface descriptors instead of adding full support for every new feature. It is **not** a security update for WinBox 3 and **does not** guarantee future RouterOS support.

## Current status

| Item | Status |
| --- | --- |
| Target legacy client | WinBox 3.43, Windows x64 |
| Target RouterOS | 7.25 (experimental compatibility) |
| Patcher input/output SHA-256 verification | Implemented |
| Local synthetic-data unit tests | **55 passing** on original local toolkit (2026-10-31); public import design has additional tests |
| Windows build and GUI launch | **Observed on the earlier local toolkit** (screenshots, 2026-10-31); revised upstream-import routine is not yet Windows-tested |
| RouterOS 7.25 connection/feature validation by this project | **Not yet documented** |
| Later RouterOS releases | **Not tested or guaranteed** |

The original patch author reports testing on a hAP ax³ with RouterOS 7.25. This is *upstream's claim*, **not** an independent lab certification by this project.

## Quick start — Windows 10/11, 64-bit

1. Download the **source ZIP**, or clone this repository. **Extract it fully**; do not run the CMD files from inside the ZIP.
2. Run `01_BUILD_WINBOX.cmd`. No Python or admin privileges are required. The builder obtains the original WinBox 3.43 x64 from the official MikroTik URL over HTTPS, or accepts a manually supplied original `winbox64.exe` in `source/`.
3. The resulting executable is created in `WinBox3_Compat/winbox64.exe` and **never committed or redistributed**.
4. Run `02_RUN_WINBOX.cmd` to verify the output digest and launch WinBox. The launcher **never supplies credentials**.
5. Use `03_VERIFY_FILES.cmd` to verify the kit's checksums.

**Only the exact original** with this SHA-256 is accepted:

```text
5b41cf51fd81e8d082687f6b522159cf4aba22e6df8edc486721d4e09507b6e9
```

Expected patched output SHA-256:

```text
ac40890431762b588a7b7777d1ad48c54751dbfa2a3868450222dce757ec496d
```

The patcher refuses unknown inputs, incorrect bytes, unexpected output digests and unsafe overwrites. **Hash verification proves byte identity, not safety or compatibility.**

A Python 3.9+ alternative is available (it also imports the pinned upstream data if not cached):

```powershell
python build_winbox.py source\winbox64.exe
```

### Important limitations

- Unknown new WinBox field types are **skipped, not implemented**; some UI controls/settings may be missing.
- WiFi Labels, BSS On Time, high-precision time fields and some routing ranges may not render correctly.
- Some PoE Power Cycle and disk Format Drive context actions may not preselect their targets. Verify the exact action target.
- Skins are disabled. Original WinBox Authenticode signature no longer validates after modification.
- CMR, future RouterOS changes, critical configuration operations, and complete IP/MAC coverage are **not verified**.
- Do **not** disable Windows Defender or SmartScreen because of this tool. Retain official WinBox 4 as a fallback and use a read-only account or lab router for initial tests.

See [full Russian instructions](README_RU.txt) and [technical compatibility notes](docs/COMPATIBILITY.md).

## Repository layout

```text
01_BUILD_WINBOX.cmd       Build with Windows PowerShell 5.1
02_RUN_WINBOX.cmd         Check hash and start local WinBox
03_VERIFY_FILES.cmd      Verify local package files
WinBox-Toolkit.ps1        PowerShell builder/runner/verifier
build_winbox.py           Optional Python builder
scripts/import_upstream.py  Import pinned upstream patch sites to local ignored source/patches.json
source/                   Place your local original EXE here (not tracked)
tests/                    55 isolated synthetic-data unit tests
scripts/package_release.py  Create a source-only ZIP for a GitHub release
.github/workflows/        Automated tests and source-only release packaging
```

## Provenance and acknowledgements

The patch-site data (downloaded only at build time into a git-ignored local file) and expected patched digest are based on **[rodenasl/winbox3-ros7-patch](https://github.com/rodenasl/winbox3-ros7-patch)**, pinned to commit [`b22d97e`](https://github.com/rodenasl/winbox3-ros7-patch/commit/b22d97ee6fb222e14ff35151634bdac42a9f5d29). The PowerShell/Python builders, packaging, validation tests and documentation were prepared separately. The original upstream patch source is **not** bundled as a file. See [NOTICE.txt](NOTICE.txt).

**Licensing note:** No upstream-derived patch bytes or executable code are committed or included in our release ZIPs. The tool obtains upstream patch data *directly from its author* during local builds; that original project had **no explicit LICENSE file at the checked revision**. Public availability is not a license. Our MIT license covers only original project-authored code and documentation. See [LEGAL.md](docs/LEGAL.md).

**Repository:** [alexsis1986/classic-winbox-compat](https://github.com/alexsis1986/classic-winbox-compat). For developer notes, see [GITHUB_SETUP.md](GITHUB_SETUP.md).

## Contributing

Compatibility reports with a **RouterOS version**, device model, WinBox client version, tested function and sanitized logs are welcome. **Never post router passwords, API tokens, IP addresses you wish to keep private, backup files, or saved WinBox sessions.**

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) and [CHANGELOG.md](CHANGELOG.md).

---

*Classic WinBox Compatibility is an independent community project. WinBox, RouterOS and MikroTik are trademarks of their respective owner(s).*
