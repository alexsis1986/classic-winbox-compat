# Compatibility and test matrix

Status is deliberately conservative. A successful local build is **not** evidence that all router operations work.

| Component | Version / platform | Evidence | Status |
| --- | --- | --- | --- |
| Builder (Python) | 3.9+; Linux runner | 59 synthetic, non-executable fixture tests; 2026-10-31 | PASS |
| Windows builder | PowerShell 5.1, Windows x64 | User screenshot with `BUILD VERIFIED` and expected output digest; 2026-10-31 | Observed on earlier local kit (not new importer) |
| Classic WinBox GUI | WinBox 3.43 x64, patched | User screenshot showing `WinBox (64bit) v3.43` open; 2026-10-31 | Observed on earlier local kit (not new importer) |
| RouterOS connection | RouterOS 7.25 | Original patch author reports hAP ax³ connectivity; not independently reproduced here | Upstream-reported only |
| IP and MAC login | RouterOS 7.25 | No project-owned test report yet | Unverified |
| Modern router features | WiFi, Containers, advanced routing, CMR | Known unknown descriptor types; feature coverage incomplete | Not guaranteed |
| RouterOS 7.26+ | Future builds | No project-owned reports | Unverified |

## How to contribute a useful report

Report: RouterOS exact version/build/channel, router model, patched-client SHA-256, connection method (IP or MAC, *not* actual address), whether login worked, features tested, and any crashes. If logs are necessary, redact identifying data and secrets first. Do not upload `autosupout.rif`, WinBox session files, live exports, backups or credentials publicly without thoroughly reviewing and sanitizing them.

Before declaring a release compatible, validate in a lab: login/logout, sidebar/menus, interface views, read-only routing/firewall info, safe mode, disconnect/reconnect, and correct target selection for destructive menu actions. Critical configuration changes should continue to use official WinBox 4.
