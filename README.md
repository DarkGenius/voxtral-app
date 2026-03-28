# Voxtral TTS

Text-to-speech на базе модели [Voxtral-4B-TTS-2603](https://huggingface.co/mistralai/Voxtral-4B-TTS-2603) от Mistral AI.

Поддерживает 9 языков: английский, французский, испанский, немецкий, итальянский, португальский, нидерландский, арабский и хинди.

## Требования

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) — менеджер пакетов

### Требования к GPU

| Режим | GPU | VRAM |
|---|---|---|
| Server | GPU нужен только серверу vLLM | >= 16 GB |
| Offline | Обязателен | >= 16 GB |

Модель весит ~8 GB в BF16. Подойдут карты уровня NVIDIA RTX 4090, A100, H100, L40S и аналогичные.

> **Примечание:** vLLM и offline mode работают только на **Linux**. На Windows можно использовать server mode, подключаясь к vLLM-серверу на удалённой Linux-машине или в WSL.

## Установка

```bash
# Базовые зависимости (только server mode)
uv sync

# С поддержкой offline mode
uv sync --extra offline
```

## Скачивание модели

Модель скачивается автоматически при первом запуске. Чтобы скачать заранее:

```bash
uv run huggingface-cli download mistralai/Voxtral-4B-TTS-2603
```

Если модель требует принятия лицензии на HuggingFace, сначала авторизуйтесь:

```bash
uv run huggingface-cli login
```

## Запуск

### Server mode (по умолчанию)

Сначала запустите vLLM-сервер:

```bash
uv run vllm-omni serve mistralai/Voxtral-4B-TTS-2603 --omni
```

Затем в другом терминале:

```bash
uv run voxtral_tts.py -t "Hello, how are you?" -o hello.wav
```

### Web-интерфейс (Gradio)

При запущенном vLLM-сервере откройте веб-интерфейс:

```bash
uv run app.py
```

Интерфейс будет доступен по адресу `http://localhost:7860`. Позволяет вводить текст, выбирать голос и прослушивать результат прямо в браузере.

### Offline mode

Загружает модель напрямую в память GPU, сервер не нужен:

```bash
uv run voxtral_tts.py -m offline -t "Hello, how are you?" -o hello.wav
```

## Запуск в WSL (Windows)

vLLM требует Linux, поэтому на Windows используйте WSL 2 с поддержкой GPU.

### 1. Установка WSL

В PowerShell от имени администратора:

```powershell
wsl --install -d Ubuntu
```

После перезагрузки выполните `wsl` в терминале и создайте пользователя.

### 2. Проверка GPU в WSL

NVIDIA-драйвер устанавливается **только в Windows** — внутри WSL он подхватывается автоматически. Убедитесь, что GPU доступен:

```bash
nvidia-smi
```

Если команда не найдена, обновите драйвер NVIDIA в Windows до версии с поддержкой WSL 2 (>= 510).

### 3. Установка uv и зависимостей

```bash
# Установить uv
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Перейти в папку проекта (диск C монтируется как /mnt/c)
cd /mnt/e/Projects/voxtral-app

# Установить все зависимости включая offline mode
uv sync --extra offline
```

### 4. Запуск

```bash
# Offline mode — загрузка модели и генерация в одном процессе
uv run voxtral_tts.py -m offline -t "Hello from WSL!" -o hello.wav

# Или server mode — запуск сервера в одном терминале
uv run vllm-omni serve mistralai/Voxtral-4B-TTS-2603 --omni

# Генерация в другом терминале WSL
uv run voxtral_tts.py -t "Hello from WSL!" -o hello.wav
```

Выходной WAV-файл будет доступен из Windows по тому же пути (`E:\Projects\voxtral-app\hello.wav`).

## Параметры CLI

| Параметр | По умолчанию | Описание |
|---|---|---|
| `-t`, `--text` | *обязательный* | Текст для синтеза |
| `-v`, `--voice` | `neutral_female` | Голосовой пресет |
| `-o`, `--output` | `output.wav`* | Путь к выходному WAV-файлу |
| `-p`, `--play` | — | Воспроизвести аудио сразу |
| `-m`, `--mode` | `server` | Режим: `server` или `offline` |
| `--server-url` | `http://localhost:8000` | URL сервера vLLM (только server mode) |
| `--model` | `mistralai/Voxtral-4B-TTS-2603` | Имя или путь к модели |

\* Если не указаны ни `-o`, ни `--play`, аудио сохраняется в `output.wav`. С `--play` без `-o` — только воспроизведение.

## Доступные голоса

| Голос | Язык |
|---|---|
| `casual_female`, `casual_male` | English |
| `cheerful_female` | English |
| `neutral_female`, `neutral_male` | English |
| `fr_female`, `fr_male` | French |
| `es_female`, `es_male` | Spanish |
| `de_female`, `de_male` | German |
| `it_female`, `it_male` | Italian |
| `pt_female`, `pt_male` | Portuguese |
| `nl_female`, `nl_male` | Dutch |
| `ar_male` | Arabic |
| `hi_female`, `hi_male` | Hindi |

## Примеры

```bash
# Сохранить в файл
uv run voxtral_tts.py -t "What a wonderful day!" -v cheerful_female -o cheerful.wav

# Воспроизвести сразу
uv run voxtral_tts.py -t "Bonjour, comment allez-vous?" -v fr_female --play

# Сохранить и воспроизвести
uv run voxtral_tts.py -t "Guten Tag!" -v de_male -o guten_tag.wav --play

# Offline mode
uv run voxtral_tts.py -m offline -t "Hello!" --play
```

## Лицензия

Модель распространяется под лицензией [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/) (только некоммерческое использование).
