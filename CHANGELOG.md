# Changelog

## [1.0.0] — 2026-10-31

**Initial compatibility toolkit, RouterOS 7.25 / WinBox 3.43 x64**

- Pin exact official input SHA-256 and expected patched output SHA-256.
- Apply 20 patches across 12 logical groups with preimage checks; recalculate PE checksum.
- Add Windows PowerShell build/launch/verification commands, optional Python builder, and local icon-cache detection.
- Fail closed on unexpected input, mismatched patch bytes, mismatched output or overwrite attempts.
- Include synthetic-data unit tests, local import verification, source-only packaging and documentation.
- Fetch upstream patch text by pinned commit, verify bytes locally without bundling unlicensed code.
- User screenshot confirms local Windows build and GUI start. **Does not independently confirm RouterOS connection.**
- Credit original patch-site research by rodenasl. See NOTICE.txt and docs/LEGAL.md.

No official MikroTik binary or icon artwork is distributed.
