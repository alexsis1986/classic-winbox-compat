# Legal, trademark and third-party notices

This is **not legal advice**. Distribution, modification, and reverse engineering may be subject to licensing terms and local laws, including limited statutory interoperability exceptions. Public GitHub visibility does **not** confer a license.

1. **MikroTik**: WinBox, RouterOS, associated names, official EXEs and icon sprites belong to MikroTik or their owners. No EXE, official artwork or trademarked logo is included in this repository or its planned ZIP releases. Users must obtain the official client themselves. The project's title describes compatibility only, without implying affiliation.
2. **Upstream patch research**: Machine-code patches from [rodenasl/winbox3-ros7-patch](https://github.com/rodenasl/winbox3-ros7-patch) commit [`b22d97e`](https://github.com/rodenasl/winbox3-ros7-patch/commit/b22d97ee6fb222e14ff35151634bdac42a9f5d29) have **no explicit redistribution license in the checked revision**. This repository does **not** contain those machine-code bytes or any copy of upstream's Python code. The local builder fetches that source from the author's pinned commit and extracts data after validation. Downloading source does not itself grant licensing rights. Seek permission/legal guidance before republishing that data.

3. **Project-authored code**: The LICENSE (MIT) covers the separately authored wrappers, builder logic, tests and original project documentation only. It does **not** cover locally imported upstream patch bytes, WinBox binaries or artwork.
4. **No warranties**: The checksum and synthetic unit tests cannot establish malware safety, crash-free operation, secure authentication, or complete compatibility.

Primary references:
- Official tools: https://mikrotik.com/download/tools
- Official WinBox 3.43 x64 binary: https://download.mikrotik.com/routeros/winbox/3.43/winbox64.exe
- Upstream patcher: https://github.com/rodenasl/winbox3-ros7-patch
- EU Software Directive 2009/24/EC, Article 6: https://eur-lex.europa.eu/eli/dir/2009/24/oj
