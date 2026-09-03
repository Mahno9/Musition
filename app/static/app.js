// Forms are generated from these schemas — every field name is the exact
// keyword argument the worker passes to the model.
const N = (k, label, v, min, max, step, hint) =>
  ({ k, label, v, min, max, step, hint, t: 'num' });
const R = (k, label, v, min, max, step, hint) =>
  ({ k, label, v, min, max, step, hint, t: 'range' });
const C = (k, label, v, hint) => ({ k, label, v, hint, t: 'bool' });
const T = (k, label, v, hint) => ({ k, label, v, hint, t: 'text' });
const A = (k, label, v, hint) => ({ k, label, v, hint, t: 'area' });
const S = (k, label, v, opts, hint) => ({ k, label, v, opts, hint, t: 'sel' });
const F = (k, label, hint) => ({ k, label, hint, t: 'file' });

const MODELS = {
  'audiogen': {
    label: 'AudioGen',
    note: 'Веса facebook/audiogen-medium — CC-BY-NC: результаты только для некоммерческого использования.',
    about: `
      <p><b>Звуковые эффекты и окружение по текстовому описанию.</b> Лает собака, шаги по гравию,
      скрип двери, гул толпы, дождь по крыше, проезжающая машина.</p>
      <ul>
        <li><b>Берите её,</b> когда нужен конкретный бытовой звук или эмбиент-подложка,
            а качество записи не критично.</li>
        <li><b>Не берите</b> для музыки и речи — она их не умеет вовсе.</li>
        <li>Один звук на промпт получается заметно чище, чем сцена из трёх событий сразу.</li>
        <li>Потолок модели — 16 kHz моно, для чистовой дорожки звук придётся дообработать.
            До 10 секунд генерируется одним куском, дальше модель дописывает продолжение.</li>
      </ul>`,
    main: [
      T('prompt', 'Промпт', 'a dog barking and footsteps on gravel'),
      R('duration', 'Длительность, с', 5, 1, 30, 1),
    ],
    groups: [
      ['Сэмплирование', [
        C('use_sampling', 'use_sampling', true, 'Выкл — жадный декод, детерминированный и однообразный'),
        N('temperature', 'temperature', 1.0, 0, 3, 0.05),
        N('top_k', 'top_k', 250, 0, 2048, 1),
        N('top_p', 'top_p', 0.0, 0, 1, 0.01, '0 — top_p выключен, работает top_k'),
      ]],
      ['Guidance', [
        N('cfg_coef', 'cfg_coef', 3.0, 0, 20, 0.1),
        C('two_step_cfg', 'two_step_cfg', false, 'Два прохода вместо батча — медленнее, иногда чище'),
      ]],
      ['Сид', [T('seed', 'seed', '', 'Пусто или -1 — случайный')]],
    ],
  },

  'stable-audio-open': {
    label: 'Stable Audio Open',
    note: 'Лицензия Stability AI: бесплатно при доходе студии < $1M/год, иначе нужна Enterprise-лицензия.',
    about: `
      <p><b>Тот же звуковой дизайн, но 44.1 kHz стерео</b> — плюс короткие инструментальные куски
      до 47 секунд.</p>
      <ul>
        <li><b>Берите её,</b> когда важно качество записи и стерео: атмосферы, лупы, ударные,
            инструментальные наброски, «красивый» звуковой дизайн.</li>
        <li>Промпт понимает жанр, инструменты, настроение и BPM — пишите как тег-лист,
            а не предложением.</li>
        <li><b>Не берите</b> для вокала и речи — их модель не генерирует.</li>
        <li>Есть продолжение аудио: подсуньте свой файл в «Продолжение аудио», и генерация
            оттолкнётся от него, а не от чистого шума.</li>
      </ul>`,
    main: [
      T('prompt', 'Промпт', 'a warm ambient pad with soft wind'),
      R('audio_end_in_s', 'Длительность, с', 10, 1, 47, 1),
    ],
    groups: [
      ['Качество', [
        N('num_inference_steps', 'num_inference_steps', 100, 1, 500, 1),
        N('guidance_scale', 'guidance_scale', 7.0, 0, 20, 0.1),
        T('negative_prompt', 'negative_prompt', 'Low quality.'),
      ]],
      ['Вариативность', [
        T('seed', 'seed', '0', 'Пусто или -1 — случайный'),
        N('num_waveforms_per_prompt', 'num_waveforms_per_prompt', 1, 1, 8, 1,
          'Сколько вариантов за один прогон — каждый попадёт в галерею отдельной записью'),
      ]],
      ['Продолжение аудио (audio2audio)', [
        F('ref_audio_path', 'Референс-файл', 'initial_audio_waveforms — генерация продолжит/переработает этот звук'),
      ]],
    ],
  },

  'bark': {
    label: 'Bark',
    about: `
      <p><b>Речь и всё, что человек издаёт помимо слов</b> — смех, вздохи, покашливание, мычание,
      напевание. Не музыкальная модель.</p>
      <ul>
        <li><b>Берите её</b> для озвучки реплик, «живых» вокализаций и звуков персонажа;
            271 пресет голоса, 13 языков, русский в том числе.</li>
        <li>Модель нестабильна по своей природе: тот же текст с другим сидом даёт другую
            интонацию и темп. Нормальная практика — сделать несколько дублей и выбрать.</li>
        <li>За раз тянет примерно 13 секунд — по сути одну-две фразы. Длинный текст режьте
            на реплики.</li>
        <li>24 kHz моно, лицензия MIT — результаты можно использовать коммерчески.</li>
      </ul>`,
    main: [
      A('text', 'Текст', '[laughs] Hey, this is Bark running locally. [sighs] Not bad!',
        'Спецтеги: [laughs] [sighs] [music] [gasps] [clears throat] [breathes]; «…» — запинка, ЗАГЛАВНЫЕ — акцент, ♪ вокруг строки — напеть её.'),
      S('voice', 'Голос (пресет)', 'v2/en_speaker_6', [], 'Список подгружается из assets/prompts'),
    ],
    groups: [
      ['Температура генерации', [
        N('text_temp', 'text_temp', 0.7, 0, 1.5, 0.05),
        N('waveform_temp', 'waveform_temp', 0.7, 0, 1.5, 0.05),
      ]],
      ['Сид', [T('seed', 'seed', '', 'Пусто или -1 — случайный')]],
    ],
  },

  'ace-step': {
    label: 'ACE-Step',
    about: `
      <p><b>Целая песня до 4 минут: вокал плюс инструментал, 48 kHz стерео.</b> Самая быстрая
      здесь относительно длины — четырёхминутный трек считается около 30 секунд.</p>
      <ul>
        <li><b>Берите её</b> для демо-треков, джинглов, фоновой музыки и вокальных набросков.</li>
        <li>Стиль задаётся тег-листом (жанр, инструменты, BPM, настроение), структура песни —
            тегами <code>[verse]</code>, <code>[chorus]</code>, <code>[bridge]</code>.
            Пустая лирика даёт инструментал.</li>
        <li>Единственная здесь модель, которая умеет <b>дорабатывать</b> готовое: перегенерировать
            кусок трека (repaint), сменить стиль или текст, сохранив мелодию (edit),
            оттолкнуться от референса (audio2audio).</li>
        <li>Apache 2.0 — коммерческое использование без ограничений.</li>
      </ul>`,
    main: [
      T('prompt', 'Стиль / теги', 'funk, pop, soul, rock, melodic, guitar, drums, bass, keyboard, percussion, 105 BPM, energetic, upbeat, groovy, vibrant, dynamic'),
      A('lyrics', 'Текст песни', '[verse]\nNeon lights they flicker bright\nCity hums in dead of night\n\n[chorus]\nWe are electric dreams tonight',
        'Структурные теги: [verse] [chorus] [bridge] [inst]. Пусто — инструментал.'),
      R('audio_duration', 'Длительность, с', 60, 10, 240, 1),
    ],
    groups: [
      ['Диффузия', [
        N('infer_step', 'infer_step', 60, 1, 200, 1),
        N('guidance_scale', 'guidance_scale', 15.0, 0, 30, 0.1),
        S('scheduler_type', 'scheduler_type', 'euler', ['euler', 'heun', 'pingpong']),
        S('cfg_type', 'cfg_type', 'apg', ['apg', 'cfg', 'cfg_star']),
        N('omega_scale', 'omega_scale', 10.0, 0, 50, 0.1),
        N('guidance_interval', 'guidance_interval', 0.5, 0, 1, 0.01),
        N('guidance_interval_decay', 'guidance_interval_decay', 0.0, 0, 1, 0.01),
        N('min_guidance_scale', 'min_guidance_scale', 3.0, 0, 30, 0.1),
        T('oss_steps', 'oss_steps', '', 'Список шагов через запятую, напр. 16,29,52 — пусто — выкл'),
      ]],
      ['Влияние текста / лирики', [
        N('guidance_scale_text', 'guidance_scale_text', 0.0, 0, 20, 0.1, '> 0 включает двойной CFG по тегам и лирике'),
        N('guidance_scale_lyric', 'guidance_scale_lyric', 0.0, 0, 20, 0.1),
        C('use_erg_tag', 'use_erg_tag', true),
        C('use_erg_lyric', 'use_erg_lyric', true),
        C('use_erg_diffusion', 'use_erg_diffusion', true),
      ]],
      ['Сид и вариативность', [
        T('manual_seeds', 'manual_seeds', '', 'Через запятую, по одному на элемент батча. Пусто — случайные'),
        T('retake_seeds', 'retake_seeds', ''),
        N('retake_variance', 'retake_variance', 0.5, 0, 1, 0.01),
        N('batch_size', 'batch_size', 1, 1, 4, 1, 'Каждый трек попадёт в галерею отдельной записью'),
      ]],
      ['Режимы', [
        S('task', 'task', 'text2music', ['text2music', 'repaint', 'edit'],
          'repaint и edit требуют исходный трек в src_audio_path'),
        C('audio2audio_enable', 'audio2audio', false),
        F('ref_audio_input', 'Референс-трек (audio2audio)'),
        N('ref_audio_strength', 'ref_audio_strength', 0.5, 0, 1, 0.01),
        F('src_audio_path', 'Исходный трек (repaint / edit)'),
        N('repaint_start', 'repaint_start, с', 0, 0, 240, 1),
        N('repaint_end', 'repaint_end, с', 0, 0, 240, 1),
        T('edit_target_prompt', 'edit_target_prompt', ''),
        A('edit_target_lyrics', 'edit_target_lyrics', ''),
        N('edit_n_min', 'edit_n_min', 0.0, 0, 1, 0.01),
        N('edit_n_max', 'edit_n_max', 1.0, 0, 1, 0.01),
        N('edit_n_avg', 'edit_n_avg', 1, 1, 10, 1),
      ]],
      ['LoRA', [
        S('lora_name_or_path', 'lora_name_or_path', 'none',
          ['none', 'ACE-Step/ACE-Step-v1-chinese-rap-LoRA'], 'Скачается при первом использовании'),
        N('lora_weight', 'lora_weight', 1.0, 0, 2, 0.05),
      ]],
    ],
  },
};

const LINKS = {
  'hunyuan': {
    label: 'Hunyuan-Foley ↗',
    title: 'HunyuanVideo-Foley (Tencent)',
    body: `<p>Локально не разворачивался: 18.6 GB весов и разработка в первую очередь под Linux —
           нет гарантии, что соберётся нативно на Windows. Вместо установки — официальный
           бесплатный Space.</p>
           <p><a href="https://huggingface.co/spaces/tencent/HunyuanVideo-Foley" target="_blank" rel="noopener">
           Открыть HunyuanVideo-Foley на Hugging Face →</a></p>`,
  },
  'yue': {
    label: 'YuE ↗',
    title: 'YuE',
    body: `<p>Пропущен: для полноценной генерации песни нужно 24 GB VRAM (комфортно — 80 GB),
           у нас 12 GB. Единственное community-демо на HF в нерабочем состоянии.</p>
           <ul>
             <li><a href="https://github.com/multimodal-art-projection/YuE" target="_blank" rel="noopener">
                 Официальный репозиторий YuE →</a></li>
             <li><a href="https://github.com/deepbeepmeep/YuEGP" target="_blank" rel="noopener">
                 Low-VRAM форк YuEGP (квантизация, 8–12 GB, медленнее и менее стабильно) →</a></li>
           </ul>`,
  },
};

// ------------------------------------------------------------------ рендеринг

const el = (tag, attrs = {}, ...kids) => {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'class') n.className = v;
    else if (k === 'html') n.innerHTML = v;
    else if (v !== undefined && v !== null) n.setAttribute(k, v);
  }
  kids.flat().forEach(c => n.append(c));
  return n;
};

function field(model, f) {
  const id = `${model}.${f.k}`;
  const hint = f.hint ? el('p', { class: 'hint' }, f.hint) : '';

  if (f.t === 'bool') {
    const inp = el('input', { type: 'checkbox', id });
    inp.checked = f.v;
    return el('div', {}, el('label', { class: 'chk' }, inp, f.label), hint);
  }
  if (f.t === 'file') {
    const inp = el('input', { type: 'file', id, accept: 'audio/*' });
    const out = el('span', { class: 'hint' });
    inp.dataset.path = '';
    inp.shownPath = out;   // чтобы «восстановить параметры» вернул уже загруженный файл
    inp.onchange = async () => {
      if (!inp.files[0]) { inp.dataset.path = ''; out.textContent = ''; return; }
      out.textContent = 'загрузка…';
      const fd = new FormData();
      fd.append('file', inp.files[0]);
      const r = await fetch('/api/upload', { method: 'POST', body: fd }).then(x => x.json());
      inp.dataset.path = r.path;
      out.textContent = r.path;
    };
    return el('label', { class: 'f' }, el('span', {}, f.label), inp, out, hint);
  }

  let inp;
  if (f.t === 'area') {
    inp = el('textarea', { id });
    inp.value = f.v ?? '';
  } else if (f.t === 'sel') {
    inp = el('select', { id });
    (f.opts || []).forEach(o => inp.append(el('option', { value: o }, o)));
    inp.value = f.v;
  } else if (f.t === 'range') {
    inp = el('input', { type: 'range', id, min: f.min, max: f.max, step: f.step, value: f.v });
    const val = el('output', {}, String(f.v));
    inp.oninput = () => { val.textContent = inp.value; };
    return el('label', { class: 'f' },
      el('span', {}, `${f.label}: `, val), inp, hint);
  } else if (f.t === 'num') {
    inp = el('input', { type: 'number', id, min: f.min, max: f.max, step: f.step, value: f.v });
  } else {
    inp = el('input', { type: 'text', id, value: f.v ?? '' });
  }
  return el('label', { class: 'f' }, el('span', {}, f.label), inp, hint);
}

const FIELDS = {};  // model -> [field spec]

function buildPane(name, cfg) {
  FIELDS[name] = [...cfg.main, ...cfg.groups.flatMap(([, fs]) => fs)];
  const pane = el('section', { class: 'pane', id: `pane-${name}` },
    el('h2', {}, cfg.label),
    el('div', { class: 'about', html: cfg.about }),
    cfg.note ? el('p', { class: 'note' }, '⚠ ' + cfg.note) : '',
    ...cfg.main.map(f => field(name, f)),
    ...cfg.groups.map(([title, fs]) =>
      el('details', {}, el('summary', {}, title), ...fs.map(f => field(name, f)))),
  );
  const btn = el('button', { class: 'go', id: `go-${name}` }, 'Сгенерировать');
  const status = el('div', { class: 'status', id: `st-${name}` });
  const result = el('div', { class: 'result', id: `res-${name}` });
  btn.onclick = () => generate(name);
  pane.append(btn, status, result);
  return pane;
}

function readParams(name) {
  const p = {};
  for (const f of FIELDS[name]) {
    const n = document.getElementById(`${name}.${f.k}`);
    if (!n) continue;
    if (f.t === 'bool') p[f.k] = n.checked;
    else if (f.t === 'file') { if (n.dataset.path) p[f.k] = n.dataset.path; }
    else if (f.t === 'num' || f.t === 'range') p[f.k] = n.value === '' ? f.v : Number(n.value);
    else p[f.k] = n.value;
  }
  return p;
}

function writeParams(name, p) {
  for (const f of FIELDS[name]) {
    if (!(f.k in p)) continue;
    const n = document.getElementById(`${name}.${f.k}`);
    if (!n) continue;
    if (f.t === 'file') {
      n.value = '';
      n.dataset.path = p[f.k] || '';
      n.shownPath.textContent = p[f.k] ? p[f.k] + ' (из прошлой генерации)' : '';
    } else if (f.t === 'bool') n.checked = !!p[f.k];
    else { n.value = p[f.k] ?? ''; n.dispatchEvent(new Event('input')); }
  }
}

// ------------------------------------------------------------------ генерация

let busyWith = null;

async function generate(name) {
  const st = document.getElementById(`st-${name}`);
  const res = document.getElementById(`res-${name}`);
  st.className = 'status';
  st.textContent = 'запуск…';
  res.textContent = '';
  const t0 = Date.now();
  const tick = setInterval(() => paintStatus(st, t0), 700);
  refreshStatus();
  try {
    const r = await fetch('/api/generate', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ model: name, params: readParams(name) }),
    });
    const data = await r.json();
    if (!r.ok) throw new Error(data.detail || r.statusText);
    st.textContent = `готово за ${((Date.now() - t0) / 1000).toFixed(1)} с`;
    data.forEach(row => res.append(card(row)));
    loadGallery();
  } catch (e) {
    st.className = 'status err';
    st.textContent = 'Ошибка: ' + e.message;
  } finally {
    clearInterval(tick);
    refreshStatus();
  }
}

function paintStatus(st, t0) {
  const s = window._slot || {};
  const secs = ((Date.now() - t0) / 1000).toFixed(0);
  const stage = { starting: 'запуск воркера', loading: 'загрузка модели в VRAM',
                  generating: 'генерация', unloading: 'выгрузка предыдущей модели' }[s.stage] || s.stage || '…';
  st.textContent = `${stage} — ${secs} с` + (s.progress != null ? ` · ${s.progress}%` : '');
  if (s.progress != null && s.stage === 'generating') {
    const bar = el('progress', { value: s.progress, max: 100 });
    st.append(el('div', {}, bar));
  }
}

async function refreshStatus() {
  try {
    const s = await fetch('/api/status').then(r => r.json());
    window._slot = s;
    busyWith = s.busy ? s.model : null;
    document.getElementById('slot').textContent = s.model
      ? `в VRAM: ${MODELS[s.model].label} · ${s.stage}`
      : 'VRAM свободна';
    for (const name of Object.keys(MODELS)) {
      const b = document.getElementById(`go-${name}`);
      const other = busyWith && busyWith !== name;
      b.disabled = !!busyWith;
      b.textContent = other ? `Занято: идёт генерация в ${MODELS[busyWith].label}`
        : busyWith ? 'Генерация…' : 'Сгенерировать';
    }
  } catch (e) { /* оркестратор перезапускается — следующий тик подхватит */ }
}

// -------------------------------------------------------------------- галерея

async function loadGallery() {
  const filter = document.getElementById('gal-filter').value;
  const list = document.getElementById('gal-list');
  const rows = await fetch('/api/gallery' + (filter ? '?model=' + filter : '')).then(r => r.json());
  list.textContent = '';
  if (!rows.length) { list.append(el('p', { class: 'hint' }, 'Пока пусто.')); return; }
  rows.forEach(row => list.append(card(row)));
}

function card(row) {
  const short = (row.prompt || '(без промпта)').slice(0, 90) + (row.prompt.length > 90 ? '…' : '');
  const box = el('div', { class: 'item' });
  const info = el('button', {}, 'Подробнее');
  info.onclick = () => openInfo(row, () => box.remove());
  box.append(
    el('div', { class: 'row' },
      el('span', { class: 'm' }, MODELS[row.model] ? MODELS[row.model].label : row.model),
      el('span', { class: 't' }, new Date(row.ts).toLocaleString()),
      el('span', { class: 't' }, row.duration ? row.duration + ' с' : ''),
      el('span', { class: 'p' }, short)),
    el('audio', { controls: '', preload: 'none', src: '/media/' + row.file }),
    el('div', {}, info));
  return box;
}

// ------------------------------------------------- окно параметров артефакта

function labelOf(model, k) {
  const f = (FIELDS[model] || []).find(x => x.k === k);
  return f && f.label !== k ? f.label : null;
}

function paramRows(model, params) {
  return Object.entries(params).map(([k, v]) => {
    const label = labelOf(model, k);
    const shown = v === '' || v === null || v === undefined ? '—'
      : typeof v === 'boolean' ? (v ? 'да' : 'нет')
      : Array.isArray(v) ? v.join(', ') : String(v);
    return el('tr', {},
      el('th', {}, label ? el('div', {}, label) : '', el('code', {}, k)),
      el('td', {}, el('pre', {}, shown)));
  });
}

function openInfo(row, onDeleted) {
  const dlg = document.getElementById('info');
  const params = JSON.parse(row.params || '{}');
  const model = MODELS[row.model] ? MODELS[row.model].label : row.model;

  dlg.querySelector('#info-title').textContent = model;
  dlg.querySelector('#info-meta').textContent =
    `${new Date(row.ts).toLocaleString()}${row.duration ? ' · ' + row.duration + ' с' : ''} · ${row.file}`;
  dlg.querySelector('#info-audio').src = '/media/' + row.file;
  const tbl = dlg.querySelector('#info-params');
  tbl.textContent = '';
  paramRows(row.model, params).forEach(tr => tbl.append(tr));
  dlg.querySelector('#info-json').textContent = JSON.stringify(params, null, 2);

  const restore = dlg.querySelector('#info-restore');
  restore.disabled = !MODELS[row.model];
  restore.onclick = () => {
    writeParams(row.model, params);
    dlg.close();
    show(row.model);
    scrollTo({ top: 0 });
  };
  dlg.querySelector('#info-delete').onclick = async () => {
    if (!confirm('Удалить запись и файл безвозвратно?')) return;
    const r = await fetch('/api/gallery/' + row.id, { method: 'DELETE' });
    if (!r.ok) { alert('Не удалось удалить: ' + r.status); return; }
    dlg.close();
    if (onDeleted) onDeleted();
    if (document.getElementById('pane-gallery').classList.contains('on')) loadGallery();
  };
  dlg.showModal();
}

function buildDialog() {
  const close = el('button', {}, 'Закрыть');
  const dlg = el('dialog', { id: 'info' },
    el('h3', { id: 'info-title' }),
    el('p', { class: 'hint', id: 'info-meta' }),
    el('audio', { id: 'info-audio', controls: '', preload: 'none' }),
    el('table', { id: 'info-params' }),
    el('details', {}, el('summary', {}, 'JSON целиком'), el('pre', { id: 'info-json' })),
    el('menu', {},
      el('button', { id: 'info-restore' }, 'Восстановить параметры в форме'),
      el('button', { id: 'info-delete', class: 'danger' }, 'Удалить'),
      close));
  close.onclick = () => dlg.close();
  dlg.onclose = () => { dlg.querySelector('#info-audio').pause(); };
  return dlg;
}

// ----------------------------------------------------------------------- tabs

function show(name) {
  document.querySelectorAll('.pane').forEach(p => p.classList.toggle('on', p.id === 'pane-' + name));
  document.querySelectorAll('#tabs button').forEach(b => b.classList.toggle('on', b.dataset.tab === name));
  location.hash = name;
  if (name === 'gallery') loadGallery();
}

function boot() {
  const tabs = document.getElementById('tabs');
  const panes = document.getElementById('panes');
  document.body.append(buildDialog());

  for (const [name, cfg] of Object.entries(MODELS)) {
    tabs.append(el('button', { 'data-tab': name }, cfg.label));
    panes.append(buildPane(name, cfg));
  }
  for (const [name, l] of Object.entries(LINKS)) {
    tabs.append(el('button', { 'data-tab': name }, l.label));
    panes.append(el('section', { class: 'pane', id: 'pane-' + name },
      el('h2', {}, l.title), el('div', { html: l.body })));
  }
  tabs.append(el('button', { 'data-tab': 'gallery' }, 'Галерея'));

  const filter = el('select', { id: 'gal-filter' }, el('option', { value: '' }, 'Все модели'),
    ...Object.entries(MODELS).map(([n, c]) => el('option', { value: n }, c.label)));
  filter.onchange = loadGallery;
  panes.append(el('section', { class: 'pane', id: 'pane-gallery' },
    el('h2', {}, 'Галерея'),
    el('label', { class: 'f' }, el('span', {}, 'Фильтр'), filter),
    el('div', { id: 'gal-list' })));

  tabs.querySelectorAll('button').forEach(b => { b.onclick = () => show(b.dataset.tab); });

  fetch('/api/voices').then(r => r.json()).then(vs => {
    const sel = document.getElementById('bark.voice');
    sel.textContent = '';
    vs.forEach(v => sel.append(el('option', { value: v }, v)));
    sel.value = vs.includes('v2/en_speaker_6') ? 'v2/en_speaker_6' : vs[0];
  }).catch(() => {});

  const start = location.hash.slice(1);
  show(MODELS[start] || LINKS[start] || start === 'gallery' ? start : 'audiogen');
  refreshStatus();
  setInterval(() => { if (!document.hidden) refreshStatus(); }, 2000);
}

boot();
