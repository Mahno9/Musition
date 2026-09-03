# Sound-gen models — local setup

4 модели развёрнуты локально (изолированный `.venv` на каждую), 2 — через готовый бесплатный
хостинг вместо локальной установки. Веса всех локальных моделей лежат на D:, не на C:.

Железо: RTX 3080 Ti (12GB VRAM). Все 4 локальные модели проверены реальной генерацией.

## Быстрый запуск

Каждая модель — отдельная папка со своим `.venv`. Активировать и запустить:

```powershell
cd c:\Projects\AI\Musition\<model>
.venv\Scripts\python.exe run.py "<промпт>" [duration]
```

Результат — `output.wav` в папке модели.

### AudioGen (Meta, SFX по тексту)
```powershell
cd c:\Projects\AI\Musition\audiogen
.venv\Scripts\python.exe run.py "a dog barking and footsteps on gravel" 5
```
- Веса: `facebook/audiogen-medium`, ~4 GB, кэш в `D:\AIModels\SoundGen\hf_cache`
- **Лицензия весов: CC-BY-NC — только некоммерческое использование.**
- Python 3.11, torch 2.1.0+cu121 (репозиторий тянет transformers 5.x, который ломает torch 2.1 —
  в venv зафиксирован `transformers==4.44.2`, см. `overrides.txt`)

### Stable Audio Open (Stability AI, SFX + короткая музыка до 47с)
```powershell
cd c:\Projects\AI\Musition\stable-audio-open
.venv\Scripts\python.exe run.py "a warm ambient pad with soft wind" 10
```
- Веса: `stabilityai/stable-audio-open-1.0` (только diffusers-часть, ~4.9 GB) в
  `D:\AIModels\SoundGen\stable-audio-open-1.0`
- **Gated-репозиторий** — лицензия принята, токен лежит в `.env` (HF_TOKEN)
- **Лицензия использования: бесплатно при доходе студии < $1M/год**, иначе Enterprise-лицензия Stability AI
- Python 3.11, torch 2.5.1+cu121, diffusers `StableAudioPipeline`

### Bark (Suno, TTS + невербальные звуки/шумы)
```powershell
cd c:\Projects\AI\Musition\bark
.venv\Scripts\python.exe run.py "[laughs] Hey, this is Bark. [sighs] Not bad!"
```
- Веса: `suno/bark`, полная версия ~11.6 GB, кэш в `D:\AIModels\SoundGen\_xdg_cache\suno`
- Лёгкая версия: переменная `SUNO_USE_SMALL_MODELS=1` перед запуском — меньше вес, быстрее, ниже качество
- Лицензия: MIT, коммерческое использование разрешено
- Python 3.11, torch 2.5.1+cu121

### ACE-Step (музыка до 4 минут, вокал + инструментал)
```powershell
cd c:\Projects\AI\Musition\ace-step
.venv\Scripts\python.exe infer.py --checkpoint_path "D:\AIModels\SoundGen\ace-step-cache\checkpoints\ACE-Step-v1-3.5B" --output_path "c:\Projects\AI\Musition\ace-step\output.wav"
```
Либо свой Gradio UI (как у остальных — через браузер):
```powershell
.venv\Scripts\acestep.exe --checkpoint_path "D:\AIModels\SoundGen\ace-step-cache\checkpoints\ACE-Step-v1-3.5B"
```
- Веса: `ACE-Step/ACE-Step-v1-3.5B`, ~7.9 GB, в `D:\AIModels\SoundGen\ace-step-cache\checkpoints`
- Лицензия: Apache 2.0, коммерческое использование без ограничений
- Python 3.11, torch 2.5.1+cu121
- **Важно:** `--output_path` указывать абсолютным путём — в коде ACE-Step баг
  (`os.path.dirname()` от голого имени файла даёт пустую строку, и `os.makedirs('')` падает на Windows)
- Скорость на 3080 Ti: полный трек (~4 мин) генерируется за ~30 секунд

## Не разворачивались локально

### HunyuanVideo-Foley (Tencent) — через хостинг
18.6 GB весов, разработка в первую очередь под Linux (нет гарантии, что соберётся нативно на
Windows). Вместо локальной установки — официальный бесплатный Space:
**https://huggingface.co/spaces/tencent/HunyuanVideo-Foley**

### YuE — пропущен
Нужно 24 GB VRAM (комфортно — 80 GB) для полноценной генерации песни; у нас 12 GB. Единственное
community-демо на HF в нерабочем состоянии. Если появится доступ к мощному GPU:
- Официальный репозиторий: https://github.com/multimodal-art-projection/YuE
- Low-VRAM community-форк (квантизация, 8-12GB, медленнее/менее стабильно): YuEGP

## Диск и кэши

Все веса и кэши пакетов переведены на D:, чтобы не забить C: (было 50GB свободно):

| Путь | Что | Размер |
|---|---|---|
| `D:\AIModels\SoundGen\hf_cache` | общий кэш HuggingFace (`HF_HOME`) | ~10.5 GB |
| `D:\AIModels\SoundGen\_xdg_cache\suno` | веса Bark | ~11.6 GB |
| `D:\AIModels\SoundGen\ace-step-cache` | веса ACE-Step | ~12.6 GB |
| `D:\AIModels\SoundGen\stable-audio-open-1.0` | веса Stable Audio Open | ~4.9 GB |
| `D:\AIModels\SoundGen\_uv_cache` | кэш пакетов pip/uv (`UV_CACHE_DIR`) | ~16.8 GB |

**Важно:** `HF_HOME` установлен через `setx` — это **глобальная** переменная окружения
пользователя Windows, не только для этого проекта. Другие ваши HF-инструменты (если
перезапустятся) тоже начнут писать кэш сюда, на D:, вместо `%USERPROFILE%\.cache\huggingface`
на C:. Пока реально этого не произошло — старые записи от других инструментов (Florence-2,
nvidia STT и пустые ref-стабы от GGUF-загрузчиков) в `hf_cache` не новые: они просто переехали
вместе со старым содержимым `C:\Users\<user>\.cache\huggingface`, когда я его туда перенёс (папка
была общая и раньше, просто на C:). Но на будущее эффект есть: если хотите вернуть дефолт —
`setx HF_HOME` без значения (или на старый путь).

В ACE-Step-кэше есть ~5 GB дублирующихся файлов (модель при первом запуске сама докачала часть
компонентов в стандартный HF-кэш поверх вручную скачанных файлов) — не мешает работе, можно
удалить `D:\AIModels\SoundGen\ace-step-cache\checkpoints\models--ACE-Step--ACE-Step-v1-3.5B`
для экономии места, если понадобится.

## Известные грабли (на будущее)

- **Нестабильный интернет:** `download-weights.ps1` и `download-sao.ps1` в корне проекта —
  скрипты докачки с `curl -C -` (резюме с реального оффсета на диске, не с оффсета на старте
  попытки) и повторной проверкой размера файла при обрыве. Штатный `huggingface_hub`/`hf` CLI
  на этой сети не годится: при обрыве начинает файл заново вместо докачки.
- **overrides.txt** в `audiogen/` — форсирует версии `av` и `numpy`, которых официально требует
  audiocraft, но для которых на Windows нет wheel-сборки под нужный Python.

## Приложение (единый UI в браузере)

```powershell
.\start.ps1          # → http://127.0.0.1:8000
```

Одна страница со вкладками на все модели: `AudioGen | Stable Audio Open | Bark |
ACE-Step | Hunyuan-Foley ↗ | YuE ↗ | Галерея`. Ручной запуск `run.py`/`infer.py` больше
не нужен, все параметры моделей выведены в форму.

### Как устроено

```
app/orchestrator.py      FastAPI на 8000: отдаёт UI, держит ОДИН слот GPU, ведёт галерею
app/workers/*.py         по воркеру на модель, каждый в своём .venv, порты 8101-8104
app/static/              страница целиком: index.html + app.js + style.css, без сборки
app/data/outputs/<model>/<uuid>.wav   результаты
app/data/gallery.db      SQLite с историей и параметрами каждой генерации
```

Воркер — HTTP-сервер на стандартной библиотеке (`http.server`), внутри venv модели ничего
доустанавливать не нужно. Эндпоинты `/status`, `/load`, `/generate`, `/unload`. Модель
остаётся в VRAM между запросами.

**12 GB VRAM хватает ровно на одну модель**, поэтому оркестратор держит единственный слот:
переключение на другую вкладку и клик «Сгенерировать» сначала гасит текущий воркер
(`/unload` → процесс выходит, VRAM освобождается полностью), потом лениво поднимает нужный.
Замер: Stable Audio Open 11.8 GB → выгрузка → Bark поднимается с 3.9 GB. Простаивающий
воркер выгружается сам через 10 минут (`IDLE_UNLOAD_S` в `orchestrator.py`).

Одновременно идёт только одна генерация: вторая получает 409, кнопки на других вкладках
блокируются с пояснением. Прогресс в процентах есть у всех четырёх (Stable Audio Open —
`callback`, ACE-Step — обёртка над его `tqdm`, AudioGen — `set_custom_progress_callback`,
Bark — только счётчик времени, у него нет колбэка).

На каждой вкладке — блок «что это за модель и когда её брать»: сильные стороны, чего модель
не умеет и что это значит для промпта.

### Галерея и окно артефакта

Все генерации вперемешку с фильтром по модели и плеером прямо в списке. Кнопка «Подробнее»
у каждого артефакта (и у только что сгенерированного, и в галерее) открывает окно, где:

- **параметры** таблицей — человеческое название плюс имя аргумента модели, и весь JSON
  отдельным блоком;
- **«Восстановить параметры в форме»** — переносит всё на вкладку модели, чтобы поменять
  только часть и перегенерировать. Возвращаются и загруженные референс-файлы, повторно
  загружать их не нужно. Случайный сид в записи сохранён уже разрешённым числом, так что
  восстановленная генерация воспроизводится точно;
- **«Удалить»** — сносит и запись, и файл, безвозвратно, с подтверждением.

### Проверка без GPU

```powershell
app\.venv\Scripts\python.exe app\test_app.py
```

Поднимает подставной воркер и проверяет протокол, вытеснение предыдущей модели, запись в
галерею, удаление файла, отказ второй параллельной генерации и автовыгрузку по простою.

### Мелочи, о которые можно споткнуться

- Bark запускается только на полных весах: они помещаются в 12 GB, если больше ничего в
  VRAM нет, а это и так гарантирует единственный слот. Переключателя
  `SUNO_USE_SMALL_MODELS` в UI нет — малые веса пришлось бы докачивать отдельно.
- ACE-Step при `batch_size > 1` перезаписывает один и тот же файл, если `save_path` — файл;
  воркер в этом случае подставляет каталог, и пайплайн пишет по файлу на элемент батча.
- `pip install` в этой сети падает на проверке сертификата (антивирус подменяет TLS) —
  venv оркестратора ставился с `--trusted-host pypi.org --trusted-host files.pythonhosted.org`.
