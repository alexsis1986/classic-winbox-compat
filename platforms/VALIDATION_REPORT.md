# Validation / Проверка — source-only platform preview

Date / дата: **2026-10-31**. Source revision: **0.1.0-preview.1**.

## Executed in this preparation environment

- Python unittest discovery: **70 test methods discovered; 62 executed successfully; 8 intentionally skipped** because `CWC_TEST_EXE` is absent.
- The 8 skipped cases require a real local proprietary payload. No such payload is needed for public-source publication.
- Launcher tests use mock Wine and a synthetic non-executable text fixture. Darwin-related branches are mocked on Linux; this is not native macOS execution.
- Checks include hash failure, missing/symlink input, no credential arguments, root denial, private-prefix behavior, paths with spaces/metacharacters, installation overwrite refusal, shell syntax and deterministic archives.
- Added publication checks cover the exact allowlist, four complete installation guides, both rights guides, unknown/session files, disguised binary/invalid UTF-8, missing files, CRLF, symlinks, locally ignored private builds, upstream manifest rejection and no output overwrites.
- Source ZIP checks cover archive CRC, exact file set and all internal SHA-256 checksums. Public source packaging is reproducible.
- Actual Linux/macOS WinBox GUI, Rosetta, Gatekeeper and router behavior: **NOT RUN / NOT VERIFIED**.

## What CI is configured to do

The separate `platforms-source.yml` runs these mock/source checks on Ubuntu and macOS runners. Only if both jobs succeed does a main-branch run publish a source-only **Pre-release**. It never downloads WinBox, Wine or upstream patch data, and never bundles an EXE.

The workflow was prepared here; its remote run and resulting release must be verified **after an actual Git push**. A prepared workflow is not evidence of successful publication. The Windows v1.0.0 tag/release is not changed.

## Windows evidence

The maintainer previously reported a successful classic WinBox connection to RouterOS 7.25, with a screenshot showing hAP be3 Media / arm64. That is user-reported evidence for the earlier Windows kit, not proof that this platform wrapper works, and the screenshot was not independently tied to an EXE digest. No screenshot, account name, MAC address or other device identifier is included in this source release.

## Русское резюме

Обнаружено 70 тестов: **62 выполнены успешно, 8 пропущены намеренно** — они требуют настоящего EXE, который не нужен для проверки публичных исходников. Используются искусственные данные и имитация Wine. Проверены запускатели, упаковка, список разрешённых файлов, отсутствие случайного включения бинарников/сессий, повторяемость ZIP и контрольные суммы.

Реальные Linux/macOS GUI, Rosetta, Gatekeeper и RouterOS здесь не проверялись. Workflow подготовлен для запуска после загрузки в GitHub; его будущий успех не объявляется заранее. Успешное Windows-подключение пользователя не заменяет тесты Linux/macOS. Юридическая чистота и отсутствие вредоносного поведения не доказываются контрольными суммами или этими тестами.
