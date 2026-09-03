# API оркестратора — вызов из консоли / другим агентом

Да: `app/orchestrator.py` — это FastAPI-сервер с готовым REST API на `http://127.0.0.1:8000`.
Он и есть UI (страница дёргает те же эндпоинты), так что можно звать напрямую — `curl`,
`Invoke-RestMethod`, любой HTTP-клиент. Скрипты изобретать не нужно.

## Запуск сервера

```powershell
cd <репозиторий>
.\start.ps1
```

Слушает `127.0.0.1:8000`, пока не остановлен (Ctrl+C). Держит один GPU-слот на все 4
модели — вторая генерация во время первой получит `409`.

## Эндпоинты

| Метод | Путь | Назначение |
|---|---|---|
| GET | `/api/status` | что сейчас загружено/крутится, прогресс |
| GET | `/api/voices` | список голосов Bark |
| POST | `/api/upload` | загрузить референс-файл, получить путь для параметров |
| POST | `/api/generate` | сгенерировать (основной вызов) |
| POST | `/api/unload` | выгрузить текущую модель из VRAM |
| GET | `/api/gallery?model=` | история генераций (`model` необязателен) |
| DELETE | `/api/gallery/{id}` | удалить запись и файл |

### GET /api/status

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/status
```

```json
{"model": "bark", "stage": "generating", "busy": true, "progress": 42.0,
 "loaded": true, "started": 1730000000.0}
```

`stage`: `idle | starting | loading | generating | unloading`.

### POST /api/generate

Тело: `{"model": "<имя>", "params": {...}}`. `out_path` подставляет сервер сам — не передавать.

```powershell
$body = @{ model = "audiogen"; params = @{ prompt = "a dog barking on gravel"; duration = 5 } } | ConvertTo-Json
Invoke-RestMethod http://127.0.0.1:8000/api/generate -Method Post -ContentType "application/json" -Body $body
```

```bash
curl -s http://127.0.0.1:8000/api/generate -H "Content-Type: application/json" \
  -d '{"model":"audiogen","params":{"prompt":"a dog barking on gravel","duration":5}}'
```

Ответ — массив записей галереи (обычно одна, у ACE-Step с `batch_size>1` — несколько):

```json
[{"id": "…", "ts": "2026-09-03T…", "model": "audiogen", "prompt": "a dog barking on gravel",
  "duration": 5, "file": "audiogen/<uuid>.wav", "params": "{…}"}]
```

Файл забирать по `http://127.0.0.1:8000/media/<file>` (например
`http://127.0.0.1:8000/media/audiogen/<uuid>.wav`), либо напрямую с диска —
`app/data/outputs/<file>`.

**Первый вызов новой модели грузит веса** (до ~120с). Переключение модели сначала
выгружает предыдущую (`/unload`, ждёт выхода процесса), потом поднимает нужную — тоже
может занять десятки секунд. Таймаут запроса на стороне оркестратора — 3600с.

Ошибки: `400` — неизвестное имя модели; `409` — уже идёт генерация; `500` — воркер
упал (текст ошибки в `detail`).

### Референс-файлы (ref_audio_path и т.п.)

Параметры, которые принимают путь к аудио (`ref_audio_path`, `ref_audio_input`,
`src_audio_path`), ждут путь **на диске сервера**. Если файл не там — сначала загрузить:

```bash
curl -s http://127.0.0.1:8000/api/upload -F "file=@C:/path/to/ref.wav"
# → {"path": "C:\\Projects\\AI\\Musition\\app\\data\\uploads\\<uuid>.wav"}
```

Полученный `path` подставить в соответствующий параметр `/api/generate`.

### POST /api/unload

```powershell
Invoke-RestMethod http://127.0.0.1:8000/api/unload -Method Post
```
`409`, если в этот момент идёт генерация. Модель и так сама выгружается через 10 минут
простоя.

### GET /api/gallery / DELETE /api/gallery/{id}

```powershell
Invoke-RestMethod "http://127.0.0.1:8000/api/gallery?model=bark"
Invoke-RestMethod "http://127.0.0.1:8000/api/gallery/<id>" -Method Delete
```

## Параметры по моделям

`model` = ключ из левой колонки. Всё, что не передано, берёт дефолт воркера.

### `audiogen` — AudioGen (SFX по тексту, до ~10-15с разумно)

| Параметр | Тип | Дефолт |
|---|---|---|
| `prompt` | string | `""` |
| `duration` | float (сек) | `5` |
| `use_sampling` | bool | `true` |
| `top_k` | int | `250` |
| `top_p` | float | `0.0` |
| `temperature` | float | `1.0` |
| `cfg_coef` | float | `3.0` |
| `two_step_cfg` | bool | `false` |
| `seed` | int (`-1`=случайный) | `-1` |

### `stable-audio-open` — SFX / музыка до ~47с

| Параметр | Тип | Дефолт |
|---|---|---|
| `prompt` | string | `""` |
| `negative_prompt` | string | нет |
| `audio_end_in_s` | float (сек, до ~47) | `10` |
| `num_inference_steps` | int | `100` |
| `guidance_scale` | float | `7.0` |
| `num_waveforms_per_prompt` | int | `1` |
| `seed` | int (`-1`=случайный) | `-1` |
| `ref_audio_path` | string (путь, см. upload) | нет — без него обычный text2audio |

### `bark` — TTS / невербальные звуки

| Параметр | Тип | Дефолт |
|---|---|---|
| `text` | string | `""` (поддерживает теги вида `[laughs]`, `[sighs]`) |
| `voice` | string, имя из `/api/voices` | нет — случайный голос |
| `text_temp` | float | `0.7` |
| `waveform_temp` | float | `0.7` |
| `seed` | int (`-1`=случайный) | `-1` |

### `ace-step` — музыка до 4 минут, вокал + инструментал

| Параметр | Тип | Дефолт |
|---|---|---|
| `task` | `text2music \| repaint \| edit` | `text2music` |
| `prompt` | string (стиль/теги) | `""` |
| `lyrics` | string | `""` |
| `audio_duration` | float (сек, до ~240) | `60` |
| `infer_step` | int | `60` |
| `guidance_scale` | float | `15.0` |
| `scheduler_type` | string | `euler` |
| `cfg_type` | string | `apg` |
| `omega_scale` | float | `10.0` |
| `manual_seeds` | string, напр. `"1, 2"` | нет (случайно) |
| `guidance_interval` | float | `0.5` |
| `guidance_interval_decay` | float | `0.0` |
| `min_guidance_scale` | float | `3.0` |
| `use_erg_tag` / `use_erg_lyric` / `use_erg_diffusion` | bool | `true` |
| `oss_steps` | — | нет |
| `guidance_scale_text` / `guidance_scale_lyric` | float | `0.0` |
| `batch_size` | int | `1` |
| `lora_name_or_path` | string | `none` |
| `lora_weight` | float | `1.0` |
| `retake_seeds` | string | нет |
| `retake_variance` | float | `0.5` |

Для `audio2audio` (продолжение/переработка трека, не отдельный `task`):
`audio2audio_enable=true` + `ref_audio_input=<путь>` (см. upload), `ref_audio_strength` (0-1, дефолт `0.5`).

Для `task=repaint` / `task=edit` нужен исходник:
`src_audio_path=<путь>`, плюс для `repaint` — `repaint_start`/`repaint_end` (int, сек, дефолт `0`),
для `edit` — `edit_target_prompt`, `edit_target_lyrics`, `edit_n_min`/`edit_n_max` (float, дефолт `0.0`/`1.0`), `edit_n_avg` (int, дефолт `1`).

## Пример полного цикла (PowerShell)

```powershell
# 1. запустить (в отдельном окне/процессе)
Start-Process powershell -ArgumentList "-NoExit","-Command","$PWD\start.ps1"
Start-Sleep 3

# 2. сгенерировать
$body = @{ model = "bark"; params = @{ text = "[laughs] Hello from an agent!" } } | ConvertTo-Json
$res = Invoke-RestMethod http://127.0.0.1:8000/api/generate -Method Post -ContentType "application/json" -Body $body

# 3. забрать файл
Invoke-WebRequest "http://127.0.0.1:8000/media/$($res[0].file)" -OutFile out.wav
```
