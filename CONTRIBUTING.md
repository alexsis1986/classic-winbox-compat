# Contributing

Thanks for helping keep classic administration workflows accessible.

- **Issues:** include exact RouterOS and WinBox versions, router model, connection method (IP/MAC), observed/expected behavior, and *sanitized* log text. Do not share credentials, public endpoints, backup files, complete exports or router session stores.
- **Pull requests:** keep changes small; explain which RouterOS feature changed and why a patch is needed. Include synthetic-data tests wherever possible. Never weaken SHA-256 verification, accept arbitrary inputs, overwrite originals or distribute an altered MikroTik executable.
- **New RouterOS versions:** run tests first, then verify a real device in a lab. Do not mark a release fully compatible based only on a build or login screen.
- **Third-party IP:** give attribution, do not submit other people's unlicensed code without permission or a clear legal basis. The locally imported manifest has separate upstream attribution; check docs/LEGAL.md.
- **Security issues:** follow SECURITY.md instead of opening public issues containing exploit details or credentials.

Target project: a safe and transparent compatibility experiment, **not** a way to bypass RouterOS authorization or privilege checks.
