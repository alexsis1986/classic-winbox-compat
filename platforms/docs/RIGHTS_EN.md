# Rights, provenance and publication boundary

This is an engineering publication policy, **not legal clearance or legal advice**. No assurance of non-infringement can be given without resolving all applicable terms and permissions.

## What this platform release contains

Original project-authored Bash launchers, installers, Python packaging/tests, CI instructions and bilingual documentation. They are licensed under the scoped MIT notice in `LICENSE`. This release contains no WinBox executable, modified executable, Wine libraries, vendor logos/icons, fonts, router packages, backups, sessions, copied upstream patch source or machine-code patch data. Hashes identify accepted local input, not a license grant.

## What remains separate

WinBox/RouterOS belong to MikroTik or the relevant owners. Wine and Apple components retain their own licenses. The earlier Windows v1.0.0 patcher and its upstream research are separate. The referenced upstream revision had no explicit redistribution license recorded in the project's checked notes. Public GitHub access and attribution are not substitutes for permission. This platform source neither fetches nor redistributes that upstream code.

A forum statement by MikroTik's normis on 2024-02-27 discusses distributing WinBox where no internal modification is required. It must **not** be treated as permission to distribute our modified EXE. Obtain explicit permission or a qualified legal assessment before redistributing modified binaries or third-party patch code. Local patching/assembly does not automatically make those activities lawful in every jurisdiction.

The private packager copies a user-supplied, exact compatible EXE into local artifacts only. It grants no right to redistribute the result. No license-key bypass or removal of vendor ownership notices is added by these platform wrappers.

## Publication controls

A file allowlist and text-only audit are used for the source release. Unknown source files are rejected outside named private-build/cache directories. Symlinks and binary contents are rejected. The workflow runs mock-only tests without downloading WinBox, Wine or upstream patches, and publishes only the source ZIP and checksum as a pre-release. It does not alter the Windows v1.0.0 tag/release.

Do not add screenshots with account/device identifiers, sessions, credentials, keys, Wine profiles, binary patches or vendor artwork. The independent project name describes compatibility only. Contributions need a documented authorship/license basis; attribution alone is insufficient. If a rights holder raises a concern, suspend the disputed distribution and review it before re-publication.

## Primary references

- GitHub licensing guidance: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository
- GitHub acceptable-use/IP rules: https://docs.github.com/en/site-policy/acceptable-use-policies/github-acceptable-use-policies
- MikroTik forum statement, 2024-02-27: https://forum.mikrotik.com/t/winbox-software-license-agreement/173850/9
- MikroTik official tools: https://mikrotik.com/download/tools

Reviewed 2026-10-31. This review addresses only this platform source addition, not a legal audit of all existing repository history.
