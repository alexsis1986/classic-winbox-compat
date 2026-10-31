# GitHub maintainer / developer setup

Repository: https://github.com/alexsis1986/classic-winbox-compat

## Clone and test locally

```sh
git clone https://github.com/alexsis1986/classic-winbox-compat.git
cd classic-winbox-compat
python scripts/import_upstream.py
python -m unittest discover -s tests -v
python scripts/package_release.py --tag v1.0.0 --output dist/ClassicWinBoxCompat-v1.0.0.zip
```

- `scripts/import_upstream.py` downloads a **pinned third-party source text** file and extracts
  machine-code patches into `source/patches.json`. That local file is ignored by Git.
- Never push generated manifests, WinBox EXEs, icon sprites, router backups or credentials.
- Do not automatically bump pins: review each new RouterOS compatibility revision.
- A GitHub tag `v*` triggers a source-only release workflow. Published builds
  are experimental and must not be presented as tested on all router models.

## Publishing / rights

The original author of upstream patch bytes has not supplied a LICENSE at
our pinned revision. Keep those bytes out of GitHub and release archives;
link to the original work instead. See [Legal notices](docs/LEGAL.md).
