# Classic WinBox Compatibility — поддержка классического WinBox

<!-- CWC_DOWNLOADS_START -->
[English](README.md) · **Русский**

## Скачать · Downloads

**Выбери свою систему — ссылки на архив и инструкции сразу здесь.**

| Платформа | Скачать | Установка / Installation |
| :--- | :--- | :--- |
| **Windows 10/11 · x64** | **[Скачать Windows-сборщик — v1.0.0](https://github.com/alexsis1986/classic-winbox-compat/releases/download/v1.0.0/ClassicWinBoxCompat-v1.0.0.zip)** | [Русский](README.ru.md#windows-setup) · [English](README.md#windows-setup) |
| **Linux · x86-64** | **[Скачать исходники Linux — Preview](https://github.com/alexsis1986/classic-winbox-compat/releases/download/platforms-source-v0.1.0-preview.1/ClassicWinBox343-PlatformSources-0.1.0-preview.1.zip)** | [Русский](https://github.com/alexsis1986/classic-winbox-compat/blob/main/platforms/docs/LINUX_RU.md) · [English](https://github.com/alexsis1986/classic-winbox-compat/blob/main/platforms/docs/LINUX_EN.md) |
| **macOS · Intel / Apple Silicon** | **[Скачать исходники macOS — Preview](https://github.com/alexsis1986/classic-winbox-compat/releases/download/platforms-source-v0.1.0-preview.1/ClassicWinBox343-PlatformSources-0.1.0-preview.1.zip)** | [Русский](https://github.com/alexsis1986/classic-winbox-compat/blob/main/platforms/docs/MACOS_RU.md) · [English](https://github.com/alexsis1986/classic-winbox-compat/blob/main/platforms/docs/MACOS_EN.md) |

**Windows:** скачивается сборщик совместимости, а не готовый EXE. Полностью распакуй архив и начни с `01_BUILD_WINBOX.cmd`.

**Linux и macOS:** обе ссылки ведут на **один архив исходников 0.1.0-preview.1**. В нём запускатели, локальный упаковщик и инструкции RU/EN — **не** готовое приложение, WinBox EXE или Wine. Нужны собственный совместимый локальный EXE и отдельно установленный Wine; используй инструкцию для своей системы. Это не нативный порт. Реальный запуск WinBox через Wine и подключение к роутеру на этих платформах **пока не проверены**. Для Apple Silicon нужен подходящий вариант Intel Wine с Rosetta, как описано в инструкции macOS.

**Описание выпусков:** [Windows v1.0.0](https://github.com/alexsis1986/classic-winbox-compat/releases/tag/v1.0.0) · [Linux/macOS Preview](https://github.com/alexsis1986/classic-winbox-compat/releases/tag/platforms-source-v0.1.0-preview.1) · **[Все выпуски](https://github.com/alexsis1986/classic-winbox-compat/releases)**

[Обзор платформ](https://github.com/alexsis1986/classic-winbox-compat/blob/main/PLATFORMS.md) · [Права и сторонние компоненты](https://github.com/alexsis1986/classic-winbox-compat/blob/main/platforms/docs/RIGHTS_RU.md)

---
<!-- CWC_DOWNLOADS_END -->

> **Неофициальный проект.** Не является разработкой MikroTik и не распространяет оригинальный или модифицированный `winbox64.exe`.

Цель — по возможности сохранить **привычный интерфейс WinBox 3.43 x64** для работы с RouterOS 7.25, не отказываясь от обновлений RouterOS. Патчер меняет отдельные байты официального EXE на компьютере пользователя, проверяя целостность исходника и результата по SHA-256.

**Что проверено:** 59 локальных тестов нового проекта и запуск предыдущего локального сборщика пользователем 31 октября 2026 года. Изменённый этап импорта данных на Windows ещё отдельно не проверен. **Работоспособность подключения к RouterOS и всех функций ещё не подтверждена независимыми тестами этого проекта.** Исходный автор патчей сообщает о проверке на hAP ax³ с RouterOS 7.25.

<a id="windows-setup"></a>

## Как использовать

1. Скачай Source ZIP из релиза GitHub или весь репозиторий через `Code → Download ZIP`, затем полностью распакуй папку.
2. Запусти `01_BUILD_WINBOX.cmd` на Windows 10/11 x64. При первом запуске нужен интернет: сборщик получает текст опубликованного патчера из **зафиксированного коммита** автора, проверяет контрольные суммы и извлекает данные 20 исправлений локально. Скачанный Python-код **не запускается**. Оригинальный EXE берётся с сайта MikroTik или из папки `source/`.
3. Дождись сообщения `BUILD VERIFIED`. Программа будет создана в `WinBox3_Compat\winbox64.exe`.
4. Запусти `02_RUN_WINBOX.cmd`. Он перепроверит хеш и откроет классический WinBox.
5. Для проверки всех файлов набора запусти `03_VERIFY_FILES.cmd`.

Не нужен Python, администратор или отключение антивируса. Если загрузка официального файла не работает, положи оригинальный WinBox 3.43 x64 в `source\winbox64.exe` и повтори.

**Ограничения:** патч пропускает неизвестные типы полей; не гарантирует работу новых функций RouterOS, CMR, WiFi или всех MAC/IP-подключений. Действия с дисками и PoE проверяй особенно внимательно. Оставь официальный WinBox 4 для важных настроек и тестируй сначала на нерабочем роутере или с учётной записью read-only.

Детальная инструкция: [README_RU.txt](README_RU.txt) · [Таблица совместимости](docs/COMPATIBILITY.md) · [Юридические пояснения](docs/LEGAL.md).

## Правовая сторона

В репозитории **нет EXE, иконок MikroTik или машинных байтов стороннего патча**. Оригинальный файл скачивается отдельно с официального источника; все изменения выполняются локально.

**Важно:** бинарные данные патчей из [`rodenasl/winbox3-ros7-patch`](https://github.com/rodenasl/winbox3-ros7-patch) имеют неуточнённые права на использование (в проверенной версии не было LICENSE). Наличие проекта на GitHub не означает разрешение перепубликовать чужой код. Вложенная лицензия MIT относится только к собственному коду и текстам этого проекта, а не к патчам и продуктам MikroTik.

**Репозиторий:** [alexsis1986/classic-winbox-compat](https://github.com/alexsis1986/classic-winbox-compat).

## Помощь проекту

Если новая RouterOS ломает старый интерфейс, открой Issue с версией RouterOS, моделью роутера и описанием проблемы. Пароли, реальные адреса, токены, сохранённые сессии и резервные копии публиковать нельзя.

[English README](README.md) · [CONTRIBUTING](CONTRIBUTING.md) · [SECURITY](SECURITY.md)
