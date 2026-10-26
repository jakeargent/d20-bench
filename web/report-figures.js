/* Figures render on page load from one cached request for precomputed aggregates. No dependencies. */
const NS = 'http://www.w3.org/2000/svg';
let aggregateRequest;
function aggregates() {
  if (!aggregateRequest) aggregateRequest = fetch('results.json').then(response => {
    if (!response.ok) throw new Error(`results.json (HTTP ${response.status})`);
    return response.json();
  }).catch(error => { aggregateRequest = undefined; throw error; });
  return aggregateRequest;
}
const element = (tag, text) => { const e = document.createElement(tag); if (text !== undefined) e.textContent = text; return e; };
function svgElement(tag, attrs = {}, text) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  if (text !== undefined) e.textContent = text;
  return e;
}
const sizes = ['small', 'medium', 'large'];
const isGemma = cfg => cfg.id.startsWith('gemma4-');
const mode = cfg => cfg.id === 'qwen3.8-27b/on' ? 'on (low)' : cfg.id.split('/')[1];
const modeLabel = cfg => ({'on (low)': 'Thinking on (low effort)', low: 'Low effort (cannot turn thinking off)', native: 'Thinking on (cannot turn thinking off)', on: 'Thinking on', off: 'Thinking off'})[mode(cfg)];
const rowName = cfg => `${cfg.model} · ${mode(cfg)}`;
/* The one number formatter: measured (floating-point) values to 3 significant digits. Counts and denominators are printed as they are. */
function sig(n) {
  if (n === null || n === undefined) return 'unknown';
  n = Number(n);
  if (n === 0) return '0';
  const r = Number(n.toPrecision(3));
  return Math.abs(r) >= 1000 ? String(r) : r.toPrecision(3);
}
/* Size ranges use two significant digits, as in the report text (2.7–5.1B, 8.0–9.7B, 24–31B). */
const range = n => Number(n).toPrecision(2);
const tick = n => String(Number(n.toPrecision(3)));
function describe(cfg, cell) {
  const q = cell.quality, t = cell.timing, o = cell.output_tokens;
  return [
    `${cfg.model} · ${modeLabel(cfg)} · ${cfg.size_class}`,
    `${cell.condition === 'supplied_passage' ? 'With oracle passages' : 'Without oracle passages'} · ${cell.records} records`,
    `Mean claim score: ${sig(q.mean_claim_score)}/100 (n=${q.exact_claim_scores})`,
    `Fully correct: ${q.fully_correct}/${q.profile_assessed}`,
    `Material errors: ${q.answers_with_material_errors}/${q.material_error_assessed}`,
    `Median: ${sig(t.median_seconds)} s · p95: ${sig(t.p95_seconds)} s (n=${t.recorded_cases})`,
    `Above 30 s: ${t.above_30_seconds}/${t.recorded_cases}`,
    `Mean output: ${sig(o.mean)} tokens (n=${o.count})`
  ];
}
/* Focus dimming: every mark, whisker and joining line carries a group (one configuration, or an off/on pair); hovering or focusing a marker dims the rest. */
const groupOf = cfg => cfg.id.replace(/\/(off|on)$/, '');
function mark(ctx, group, el) {
  el.dataset.group = group; ctx.marks.push(el); ctx.svg.append(el); return el;
}
function highlight(ctx, group) {
  ctx.svg.classList.add('has-focus');
  for (const el of ctx.marks) el.classList.toggle('in-focus', el.dataset.group === group);
}
function unhighlight(ctx) {
  ctx.svg.classList.remove('has-focus');
  for (const el of ctx.marks) el.classList.remove('in-focus');
}
function shape(size, x, y, open, cls = 'mark') {
  const attrs = { class: cls, fill: open ? 'var(--paper)' : 'currentColor', stroke: 'currentColor', 'stroke-width': 1.5 };
  if (size === 'small') return svgElement('circle', { ...attrs, cx: x, cy: y, r: 4 });
  if (size === 'medium') return svgElement('rect', { ...attrs, x: x-4, y: y-4, width: 8, height: 8 });
  return svgElement('path', { ...attrs, d: `M${x},${y-5}l5,9h-10Z` });
}
/* Markers carry the exact values in aria-label (no SVG <title>, which would add a native tooltip over the styled one). */
function point(ctx, cfg, cell, x, y, open, group = cfg.id) {
  const lines = describe(cfg, cell);
  const g = svgElement('g', { class: 'point' + (isGemma(cfg) ? ' gemma' : ''), tabindex: -1, role: 'graphics-symbol', 'aria-label': lines.join('. ') });
  g.append(svgElement('circle', { class: 'hit', cx: x, cy: y, r: 10 }), shape(cfg.size_class, x, y, open));
  const text = lines.join('\n'), { tip, readout, figure, points } = ctx;
  function show() {
    highlight(ctx, group);
    tip.textContent = text; tip.hidden = false;
    readout.textContent = lines.join(' · ');
    const box = g.getBoundingClientRect(), frame = figure.getBoundingClientRect();
    const size = tip.getBoundingClientRect();
    tip.style.left = `${Math.max(0, Math.min(box.left-frame.left, frame.width-size.width))}px`;
    const below = box.bottom-frame.top+10;
    tip.style.top = `${box.bottom+10+size.height > innerHeight && box.top-size.height-10 > 0 ? box.top-frame.top-size.height-10 : below}px`;
  }
  const hide = () => { tip.hidden = true; unhighlight(ctx); };
  const move = to => { const next = points[Math.max(0, Math.min(points.length-1, to))]; if (next) next.focus(); };
  g.addEventListener('mouseenter', show); g.addEventListener('mouseleave', hide);
  g.addEventListener('focus', () => { for (const p of points) p.tabIndex = p === g ? 0 : -1; show(); });
  g.addEventListener('blur', hide);
  g.addEventListener('keydown', e => {
    const i = points.indexOf(g), step = { ArrowRight: 1, ArrowDown: 1, ArrowLeft: -1, ArrowUp: -1 }[e.key];
    if (e.key === 'Escape') hide();
    else if (step) { e.preventDefault(); move(i+step); }
    else if (e.key === 'Home') { e.preventDefault(); move(0); }
    else if (e.key === 'End') { e.preventDefault(); move(points.length-1); }
  });
  points.push(g); return mark(ctx, group, g);
}
function legendKey(size, text, open, gemma) {
  const key = element('span'); key.className = 'key' + (gemma ? ' gemma' : '');
  const mark = svgElement('svg', { viewBox: '0 0 12 12', width: 12, height: 12, 'aria-hidden': 'true' });
  mark.append(shape(size, 6, 6, open, 'mark')); key.append(mark, document.createTextNode(text)); return key;
}
function legend(plot, data, states) {
  const p = element('p'); p.className = 'figure-legend';
  for (const size of sizes) {
    const b = data.configurations.filter(c => c.size_class === size).map(c => c.total_parameters/1e9);
    p.append(legendKey(size, `${size} ${range(Math.min(...b))}–${range(Math.max(...b))}B`));
  }
  p.append(legendKey('small', 'Gemma 4', false, true));
  if (states.length) { const br = element('span'); br.className = 'break'; p.append(br); }
  for (const [open, text] of states) p.append(legendKey('small', text, open));
  plot.append(p);
}
function niceTicks(max) {
  const raw = max/4, mag = 10**Math.floor(Math.log10(raw));
  const step = [1, 2, 2.5, 5, 10].map(m => m*mag).find(s => s >= raw), out = [];
  for (let v = 0; v <= max+1e-9; v += step) out.push(v);
  return out;
}
const timeTicks = max => [0, 1, 5, 30, 100, 300, 900].filter(v => v <= max);
const timeScale = (max, a, b) => v => a + (b-a)*Math.log1p(v)/Math.log1p(max);
const linearScale = (max, a, b) => v => a + (b-a)*v/max;
const svgFor = (ctx, W, H) => {
  const svg = svgElement('svg', { viewBox: `0 0 ${W} ${H}`, width: W, height: H, role: 'group', 'aria-label': ctx.title });
  ctx.svg = svg; ctx.chart.append(svg); return svg;
};
const line = (svg, cls, x1, y1, x2, y2) => svg.append(svgElement('line', { x1, x2, y1, y2, class: cls }));
const text = (svg, x, y, s, anchor, cls) => svg.append(svgElement('text', { x, y, ...(anchor ? { 'text-anchor': anchor } : {}), ...(cls ? { class: cls } : {}) }, s));
function tickLabels(svg, scale, ticks, y, max) {
  for (const n of ticks) text(svg, scale(n), y, tick(n), n === 0 ? 'start' : n === max ? 'end' : 'middle');
}
/* Rows: one line per configuration, ordered by size class then total parameters. Narrow widths put the label above the track. */
const rowLayout = W => W < 560 ? { narrow: true, labelW: 0, rowH: 38, x0: 10 } : { narrow: false, labelW: 166, rowH: 22, x0: 174 };
function rowFrame(svg, configs, L, top, W) {
  const place = i => {
    const y0 = top + i*L.rowH;
    return L.narrow ? { label: y0 + 11, track: y0 + 27 } : { label: y0 + L.rowH/2 + 4, track: y0 + L.rowH/2 };
  };
  configs.forEach((cfg, i) => {
    if (i && cfg.size_class !== configs[i-1].size_class) line(svg, 'group-rule', 0, top + i*L.rowH, W, top + i*L.rowH);
    text(svg, 0, place(i).label, rowName(cfg), undefined, 'row-label');
  });
  return place;
}
function oracleEffect(ctx, configs, cell, metric, W) {
  const get = c => metric === 'claims' ? c.quality.mean_claim_score : metric === 'seconds' ? c.timing.median_seconds : c.output_tokens.mean;
  const time = metric === 'seconds', L = rowLayout(W), x1 = W-12;
  const max = metric === 'claims' ? 100 : time ? Math.max(30, ...ctx.data.cells.map(get))*1.05 : Math.max(...ctx.data.cells.map(get))*1.05;
  const label = metric === 'claims' ? 'Mean claim score /100' : time ? 'Median completion time, s (log scale)' : 'Mean output tokens';
  const x = time ? timeScale(max, L.x0, x1) : linearScale(max, L.x0, x1);
  const ticks = time ? timeTicks(max) : niceTicks(max), axisY = time ? 42 : 24, top = axisY + 8;
  const bottom = top + configs.length*L.rowH, svg = svgFor(ctx, W, bottom + 40);
  for (const n of ticks) line(svg, 'grid', x(n), axisY, x(n), bottom);
  line(svg, 'axis', L.x0, axisY, x1, axisY); line(svg, 'axis', L.x0, bottom, x1, bottom);
  tickLabels(svg, x, ticks, axisY-8, ticks[ticks.length-1]); tickLabels(svg, x, ticks, bottom+16, ticks[ticks.length-1]);
  text(svg, L.x0, bottom+34, label);
  if (time) for (const n of [5, 30]) {
    line(svg, 'reference', x(n), 16, x(n), bottom);
    text(svg, x(n)-4, 11, n === 5 ? '5 s target' : '30 s cutoff', 'end');
  }
  const place = rowFrame(svg, configs, L, top, W);
  configs.forEach((cfg, i) => {
    const y = place(i).track, a = cell(cfg.id, 'no_source'), b = cell(cfg.id);
    mark(ctx, cfg.id, svgElement('line', { x1: x(get(a)), x2: x(get(b)), y1: y, y2: y, class: 'trace' + (isGemma(cfg) ? ' gemma' : '') }));
  });
  configs.forEach((cfg, i) => {
    const y = place(i).track;
    point(ctx, cfg, cell(cfg.id, 'no_source'), x(get(cell(cfg.id, 'no_source'))), y, true);
    point(ctx, cfg, cell(cfg.id), x(get(cell(cfg.id))), y, false);
  });
}
/* Three small dot plots share one row label column. */
function scoresAndErrors(ctx, configs, cell, W) {
  const L = rowLayout(W), gap = L.narrow ? 14 : 36, colW = (W - 12 - L.x0 - 2*gap)/3;
  const measures = [
    [L.narrow ? 'Claim /100' : 'Mean claim score /100', c => c.quality.mean_claim_score, 100],
    [L.narrow ? 'Correct /120' : 'Fully correct (count)', c => c.quality.fully_correct, 120, true],
    [L.narrow ? 'Errors /120' : 'Material errors (count)', c => c.quality.answers_with_material_errors, 120]
  ];
  const cols = measures.map(([title, get, max, half], j) => { const a = L.x0 + j*(colW+gap); return { title, get, max, half, a, x: linearScale(max, a, a+colW) }; });
  const axisY = 36, top = axisY + 8, bottom = top + configs.length*L.rowH, svg = svgFor(ctx, W, bottom + 24);
  for (const c of cols) {
    const ticks = [0, c.max/2, c.max];
    text(svg, c.a, 11, c.title);
    for (const n of ticks) line(svg, 'grid', c.x(n), axisY, c.x(n), bottom);
    if (c.half) line(svg, 'reference half', c.x(60), axisY, c.x(60), bottom);
    line(svg, 'axis', c.a, axisY, c.a+colW, axisY); line(svg, 'axis', c.a, bottom, c.a+colW, bottom);
    tickLabels(svg, c.x, ticks, axisY-8, c.max); tickLabels(svg, c.x, ticks, bottom+16, c.max);
  }
  const place = rowFrame(svg, configs, L, top, W);
  configs.forEach((cfg, i) => {
    const y = place(i).track, cl = cell(cfg.id);
    for (const c of cols) mark(ctx, cfg.id, svgElement('line', { x1: c.a, x2: c.a+colW, y1: y, y2: y, class: 'track' }));
    for (const c of cols) point(ctx, cfg, cl, c.x(c.get(cl)), y, false);
  });
}
/* Fully correct count against median completion time, with p95 whiskers or off/on pairs. */
function scatter(ctx, configs, cell, W, thinking) {
  const narrow = W < 560, H = narrow ? 320 : 380, left = 40, right = 14, top = 40, bottom = H - 44;
  const max = Math.max(30, ...configs.map(c => cell(c.id).timing.p95_seconds))*1.05;
  const x = timeScale(max, left, W-right), y = n => bottom - (bottom-top)*n/120, svg = svgFor(ctx, W, H);
  text(svg, 0, 11, 'Fully correct answers (count)');
  for (const n of [0, 30, 60, 90, 120]) { line(svg, 'grid', left, y(n), W-right, y(n)); text(svg, left-8, y(n)+4, String(n), 'end'); }
  const ticks = timeTicks(max);
  for (const n of ticks) { line(svg, 'tick', x(n), bottom, x(n), bottom+4); text(svg, x(n), bottom+18, tick(n), n === 0 ? 'start' : 'middle'); }
  line(svg, 'axis', left, bottom, W-right, bottom);
  text(svg, left, H-4, 'Completion time, s (log scale)');
  for (const n of [5, 30]) {
    line(svg, 'reference', x(n), 26, x(n), bottom);
    text(svg, x(n)-4, 24, n === 5 ? '5 s target' : '30 s cutoff', 'end');
  }
  line(svg, 'reference half', left, y(60), W-right, y(60));
  text(svg, left+6, y(60)-5, '60/120 (half)', 'start', 'reference-label');
  if (thinking) {
    for (const cfg of configs.filter(c => c.id.endsWith('/off'))) {
      const on = configs.find(c => c.id === cfg.id.slice(0, -3) + 'on'); if (!on) continue;
      const a = cell(cfg.id), b = cell(on.id), ax = x(a.timing.median_seconds), bx = x(b.timing.median_seconds);
      mark(ctx, groupOf(cfg), svgElement('line', { x1: ax, x2: bx, y1: y(a.quality.fully_correct), y2: y(b.quality.fully_correct), class: 'trace' + (isGemma(cfg) ? ' gemma' : '') }));
    }
    for (const cfg of configs.filter(c => c.id.endsWith('/off'))) {
      const on = configs.find(c => c.id === cfg.id.slice(0, -3) + 'on'); if (!on) continue;
      const a = cell(cfg.id), b = cell(on.id);
      point(ctx, cfg, a, x(a.timing.median_seconds), y(a.quality.fully_correct), true, groupOf(cfg));
      point(ctx, on, b, x(b.timing.median_seconds), y(b.quality.fully_correct), false, groupOf(cfg));
    }
  } else {
    for (const cfg of configs) {
      const c = cell(cfg.id), yy = y(c.quality.fully_correct), a = x(c.timing.median_seconds), b = x(c.timing.p95_seconds);
      const cls = 'trace' + (isGemma(cfg) ? ' gemma' : '');
      mark(ctx, cfg.id, svgElement('line', { x1: a, x2: b, y1: yy, y2: yy, class: cls }));
      mark(ctx, cfg.id, svgElement('line', { x1: b, x2: b, y1: yy-3, y2: yy+3, class: cls }));
    }
    for (const cfg of configs) { const c = cell(cfg.id); point(ctx, cfg, c, x(c.timing.median_seconds), y(c.quality.fully_correct), false); }
  }
}
function render(figure, data, metric) {
  const key = figure.id, plot = figure.querySelector('.figure-plot'); plot.replaceChildren();
  const configs = [...data.configurations].sort((a, b) => sizes.indexOf(a.size_class)-sizes.indexOf(b.size_class) || a.total_parameters-b.total_parameters || a.id.localeCompare(b.id));
  const cell = (id, condition = 'supplied_passage') => data.cells.find(c => c.configuration === id && c.condition === condition);
  const paired = key === 'oracle-effect' ? [[true, 'without oracle passages'], [false, 'with oracle passages']] : key === 'thinking-returns' ? [[true, 'thinking off'], [false, 'thinking on']] : [];
  legend(plot, data, paired);
  if (key === 'oracle-effect') {
    const label = element('label', 'Measure '), select = element('select'); select.setAttribute('aria-label', 'Oracle effect measure');
    for (const [value, text] of [['claims', 'Mean claim score'], ['seconds', 'Median completion time'], ['tokens', 'Mean output tokens']]) { const op = element('option', text); op.value = value; select.append(op); }
    select.value = metric || 'claims'; label.append(select); plot.append(label);
    select.addEventListener('change', () => { const next = select.value; render(figure, data, next); figure.querySelector('select').focus(); });
    metric = select.value;
  }
  if (key === 'live-use-tradeoffs' || key === 'thinking-returns') {
    plot.append(element('p', key === 'thinking-returns'
      ? 'Lines join each off/on pair; the dashed horizontal line marks half of the 120 cases. Focus a marker to highlight its pair and see p95, output tokens and the other exact values.'
      : 'Markers show median time; lines extend to p95; the dashed horizontal line marks half of the 120 cases. Focus a marker to highlight it and see mean output tokens and the other exact values.'));
    plot.lastChild.className = 'figure-legend';
  }
  const tip = element('div'); tip.className = 'figure-tip'; tip.hidden = true;
  const readout = element('p', 'Tab to a marker and use the arrow keys to see its exact values.'); readout.className = 'figure-readout';
  const chart = element('div'); chart.className = 'figure-chart'; plot.append(chart, readout, tip);
  const W = Math.max(260, Math.round(chart.getBoundingClientRect().width));
  const ctx = { data, tip, readout, figure, chart, points: [], marks: [], title: figure.querySelector('h3').textContent };
  if (key === 'oracle-effect') oracleEffect(ctx, configs, cell, metric, W);
  else if (key === 'scores-and-errors') scoresAndErrors(ctx, configs, cell, W);
  else if (key === 'live-use-tradeoffs' || key === 'thinking-returns') scatter(ctx, configs, cell, W, key === 'thinking-returns');
  if (ctx.points[0]) ctx.points[0].tabIndex = 0;
}
async function load(figure) {
  const status = figure.querySelector('.figure-status');
  figure.querySelector('.figure-load')?.remove();
  status.textContent = 'Loading figure…';
  try {
    const data = await aggregates(); render(figure, data); status.textContent = '';
    let width = figure.clientWidth;
    // Recompute SVG coordinates when the figure moves between paper and mobile layouts.
    new ResizeObserver(() => {
      if (figure.clientWidth === width) return;
      width = figure.clientWidth;
      render(figure, data, figure.querySelector('select')?.value);
    }).observe(figure);
  }
  catch (error) {
    status.textContent = 'Could not load figure: ' + error.message + '. Static values remain below.';
    const retry = element('button', 'Retry figure'); retry.type = 'button'; retry.className = 'figure-load';
    retry.addEventListener('click', () => load(figure)); status.after(retry);
  }
}
for (const figure of document.querySelectorAll('.interactive-figure')) load(figure);
