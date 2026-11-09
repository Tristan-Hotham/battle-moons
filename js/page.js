/* Fighting by moonlight: every dated battle in Wikidata on a plain MapLibre base map (OpenFreeMap Positron), coloured by the
 * phase of the Moon on the day at the battle site, with a phase filter, a year range, layers and a live moon-phase wheel.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:800px)').matches;
  const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
  const FIXTXT = ['Gregorian date as entered', 'Julian date, converted', 'Julian date entered with a Gregorian flag (before 1582): read as Julian and converted',
    'Old Style date entered with a Gregorian flag: checked by hand, read as Julian', 'Gregorian date in the Old Style years: checked by hand',
    'date corrected by hand (see the notes)', 'Britain, Ireland or British North America before 1752 with a Gregorian flag: may be Old Style, so left out of the test',
    'ancient date converted by modern scholars: left out of the test'];
  let map = null, P = null, S = null, feats = [], idx = {};
  const st = { y0: -600, y1: 2026, ph: new Set([0, 1, 2, 3, 4, 5, 6, 7]) };
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));
  const ytxt = y => y > 0 ? String(y) : (1 - y) + ' BC';
  const dtxt = (y, m, d) => `${d} ${MONTHS[m - 1]} ${ytxt(y)}`;
  const hm = v => v == null ? '' : String(Math.floor(((v % 1440) + 1440) % 1440 / 60)).padStart(2, '0') + ':' + String(((v % 60) + 60) % 60).padStart(2, '0');
  const pbin = a => Math.floor(((a + 22.5) % 360) / 45);

  function moonSVG(phase, r) {             // the Moon from the northern hemisphere, waxing lit on the right
    r = r || 22; const ph = ((phase % 360) + 360) % 360, side = ph < 180 ? 1 : -1, c = Math.cos((ph < 180 ? ph : 360 - ph) * Math.PI / 180);
    let d = `M 0 ${-r} A ${r} ${r} 0 0 ${side > 0 ? 1 : 0} 0 ${r} A ${Math.abs(c * r) || 0.001} ${r} 0 0 ${(c > 0) === (side > 0) ? 0 : 1} 0 ${-r} Z`;
    return `<svg viewBox="${-r - 1} ${-r - 1} ${2 * r + 2} ${2 * r + 2}" width="${2 * r + 2}" height="${2 * r + 2}" aria-hidden="true"><circle r="${r}" fill="#3A3550"/><path d="${d}" fill="#F7EBC4"/><circle r="${r}" fill="none" stroke="#2B2119" stroke-width="1"/></svg>`;
  }
  window.__moonSVG = moonSVG;

  function popup(i, ll) {
    const r = P.rows[i], C = P.c;
    const [q, label, lon, lat, y, m, d, phase, illum, fix, flags, sl, mdh, dh, sset, srise, mrise, mset, dfull, jul, war] = r;
    const b = pbin(phase);
    const df = Math.abs(dfull) < 0.5 ? 'at full moon' : (dfull < 0 ? `${(-dfull).toFixed(1)} days before full moon` : `${dfull.toFixed(1)} days after full moon`);
    const nightTxt = dh > 0 ? `The Moon was up for <b>${mdh.toFixed(1)} of ${dh.toFixed(1)} hours</b> of darkness the night before.` : 'No true darkness the night before (summer twilight).';
    const rs = [mrise.length ? 'moonrise ' + mrise.map(hm).join(', ') : '', mset.length ? 'moonset ' + mset.map(hm).join(', ') : ''].filter(Boolean).join(' · ');
    const kind = flags & 1 ? 'Siege (start date)' : (flags & 2 ? 'At sea' : 'Battle');
    const notes = [];
    if (!(flags & 4) && !(flags & 1)) notes.push(flags & 8 ? 'Wikidata gives dates more than three days apart: shown at the first, not in the test.' : 'Not in the test: ' + FIXTXT[fix] + '.');
    if (flags & 16) notes.push('Placed at the coordinates of its location.');
    new maplibregl.Popup({ maxWidth: '320px' }).setLngLat(ll).setHTML(`<div class="mp">${moonSVG(phase, 22)}<div><b class="t">${esc(label)}</b>
      <div class="nt">${esc(kind)}${war ? ' · ' + esc(war) : ''}</div></div></div>
      <table><tr><td>Date</td><td>${dtxt(y, m, d)}${jul ? `<br><span class="nt">${dtxt(jul[0], jul[1], jul[2])} in the Julian calendar</span>` : ''}</td></tr>
      <tr><td>Moon</td><td><span class="sw" style="background:${S.pcol[b]}"></span>${S.phases[b]}, ${illum}% lit, ${df}</td></tr>
      <tr><td>Night before</td><td>${nightTxt}${rs ? `<br><span class="nt">${rs}; sunset ${hm(sset)}, sunrise ${hm(srise)} (local solar time)</span>` : ''}</td></tr></table>
      <div class="nt">${esc(FIXTXT[fix])}.${notes.length ? ' ' + esc(notes.join(' ')) : ''}</div>
      <div class="lk"><a href="https://www.wikidata.org/wiki/${q}" target="_blank" rel="noopener">Wikidata ${q}</a><span class="nt">${sl} Wikipedia editions</span></div>`).addTo(map);
  }

  function filt() {
    const f = ['all', ['>=', ['get', 'y'], st.y0], ['<=', ['get', 'y'], st.y1], ['in', ['get', 'b'], ['literal', [...st.ph]]]];
    const lay = { lyT: ['==', ['get', 'k'], 0], lyS: ['==', ['get', 'k'], 1], lyU: ['==', ['get', 'k'], 2], lyG: ['==', ['get', 'k'], 3] };
    const on = Object.keys(lay).filter(id => document.getElementById(id).checked).map(id => lay[id]);
    f.push(on.length ? ['any', ...on] : ['==', 1, 0]);
    map.setFilter('pts', f); map.setFilter('pts-halo', f);
    wheel();
    document.getElementById('yr').textContent = `${ytxt(st.y0)} to ${ytxt(st.y1)}`;
  }

  function wheel() {                         // the live wheel: visible test battles by phase against random days
    const cnt = [0, 0, 0, 0, 0, 0, 0, 0]; let n = 0;
    for (const f of feats) { const p = f.properties; if ((p.k === 0 || p.k === 3) && p.y >= st.y0 && p.y <= st.y1) { cnt[p.b]++; n++; } }
    const W = 250, c = W / 2, R0 = 22, Rm = 84, mx = Math.max(...cnt.map(v => v / Math.max(n, 1)), 0.2);
    let svg = `<svg viewBox="0 0 ${W} ${W}" role="img" aria-label="Battles by phase of the Moon">`;
    for (let k = 0; k < 8; k++) {
      const a0 = (k * 45 - 22.5 - 90) * Math.PI / 180, a1 = (k * 45 + 22.5 - 90) * Math.PI / 180, sh = n ? cnt[k] / n : 0, rr = R0 + (Rm - R0) * sh / mx;
      const p = (r, a) => `${(c + r * Math.cos(a)).toFixed(1)} ${(c + r * Math.sin(a)).toFixed(1)}`;
      svg += `<path d="M ${p(R0, a0)} L ${p(rr, a0)} A ${rr} ${rr} 0 0 1 ${p(rr, a1)} L ${p(R0, a1)} A ${R0} ${R0} 0 0 0 ${p(R0, a0)} Z" fill="${S.pcol[k]}" stroke="#2B2119" stroke-width=".6" opacity="${st.ph.has(k) ? 1 : 0.25}"><title>${S.phases[k]}: ${cnt[k]} (${(100 * sh).toFixed(1)}%; random days ${S.exp_pc[k].toFixed(1)}%)</title></path>`;
    }
    const pts = []; for (let k = 0; k <= 8; k++) { const kk = k % 8, a = (kk * 45 - 90) * Math.PI / 180, rr = R0 + (Rm - R0) * (S.exp_pc[kk] / 100) / mx; pts.push(`${(c + rr * Math.cos(a)).toFixed(1)},${(c + rr * Math.sin(a)).toFixed(1)}`); }
    svg += `<polyline points="${pts.join(' ')}" fill="none" stroke="#A3261B" stroke-width="1.4" stroke-dasharray="3 2"/>`;
    [['New', 0], ['First qtr', 90], ['Full', 180], ['Last qtr', 270]].forEach(([t, a]) => { const r = 100, x = c + r * Math.sin(a * Math.PI / 180), y = c - r * Math.cos(a * Math.PI / 180) + 3; svg += `<text x="${x.toFixed(0)}" y="${y.toFixed(0)}" text-anchor="middle" class="ax">${t}</text>`; });
    svg += `<text x="${c}" y="${c + 4}" text-anchor="middle" class="lg">${n.toLocaleString('en-GB')}</text></svg>`;
    document.getElementById('wheelSvg').innerHTML = svg;
  }

  function setup() {
    const C = {}; P.cols.forEach((k, i) => C[k] = i); P.c = C;
    feats = P.rows.map((r, i) => {
      const fl = r[10], k = fl & 1 ? 1 : (fl & 4 ? (fl & 2 ? 3 : 0) : 2);
      return { type: 'Feature', properties: { i, y: r[4], b: pbin(r[7]), k, sl: r[11] }, geometry: { type: 'Point', coordinates: [r[2], r[3]] } };
    });
    const before = (map.getStyle().layers.find(l => l.type === 'symbol') || {}).id;
    map.addSource('b', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, attribution: 'Battles: <a href="https://www.wikidata.org/" target="_blank">Wikidata</a> (CC0)' });
    const col = ['match', ['get', 'b'], 0, S.pcol[0], 1, S.pcol[1], 2, S.pcol[2], 3, S.pcol[3], 4, S.pcol[4], 5, S.pcol[5], 6, S.pcol[6], S.pcol[7]];
    const radf = e => ['interpolate', ['linear'], ['zoom'], 1, ['+', 2.6 + e, ['*', 0.04, ['min', ['get', 'sl'], 60]]], 6, ['+', 4 + e, ['*', 0.06, ['min', ['get', 'sl'], 60]]], 12, ['+', 7 + e, ['*', 0.08, ['min', ['get', 'sl'], 60]]]];
    const rad = radf(0);
    map.addLayer({ id: 'pts-halo', type: 'circle', source: 'b', paint: { 'circle-radius': radf(1.4), 'circle-color': '#FFFFFF', 'circle-opacity': 0.9 } }, before);
    map.addLayer({ id: 'pts', type: 'circle', source: 'b', paint: { 'circle-radius': rad, 'circle-color': col,
      'circle-stroke-color': ['match', ['get', 'k'], 2, '#A3261B', '#2B2119'], 'circle-stroke-width': ['match', ['get', 'k'], 2, 1.4, 0.6],
      'circle-opacity': ['match', ['get', 'k'], 1, 0.75, 0.95] } }, before);
    map.addLayer({ id: 'lbl', type: 'symbol', source: 'b', minzoom: 6, filter: ['>=', ['get', 'sl'], 12], layout: { 'text-field': ['get', 'n'], 'text-size': 11, 'text-font': ['Noto Sans Italic'], 'text-offset': [0, 1.0], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#4A3B2B', 'text-halo-color': '#fff', 'text-halo-width': 1.4 } });
    feats.forEach(f => f.properties.n = P.rows[f.properties.i][1].replace(/^Battle of (the )?/, ''));
    map.getSource('b').setData({ type: 'FeatureCollection', features: feats });
    map.on('click', 'pts', e => { const f = e.features[0]; popup(f.properties.i, f.geometry.coordinates); });
    map.on('mouseenter', 'pts', () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', 'pts', () => map.getCanvas().style.cursor = '');
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    ['lyT', 'lyS', 'lyU', 'lyG'].forEach(id => document.getElementById(id).addEventListener('change', filt));
    document.getElementById('lyL').addEventListener('change', e => map.setLayoutProperty('lbl', 'visibility', e.target.checked ? 'visible' : 'none'));
    document.getElementById('lyW').addEventListener('change', e => document.getElementById('wheel').hidden = !e.target.checked);
    const pf = document.getElementById('phases');
    S.phases.forEach((nm, k) => { const l = document.createElement('label'); l.innerHTML = `<input type="checkbox" data-k="${k}" checked> <span class="mi">${moonSVG(k * 45, 9)}</span>${esc(nm)}`; pf.appendChild(l); });
    pf.addEventListener('change', e => { const k = +e.target.dataset.k; if (e.target.checked) st.ph.add(k); else st.ph.delete(k); filt(); });
    document.querySelectorAll('.chip[data-pr]').forEach(b => b.addEventListener('click', () => {
      const v = b.dataset.pr; st.ph = new Set(v === 'all' ? [0, 1, 2, 3, 4, 5, 6, 7] : v.split(',').map(Number));
      pf.querySelectorAll('input').forEach(i => i.checked = st.ph.has(+i.dataset.k));
      document.querySelectorAll('.chip[data-pr]').forEach(x => x.setAttribute('aria-pressed', x === b)); filt(); }));
    const a = document.getElementById('ya'), z = document.getElementById('yz');
    const upd = () => { let v0 = +a.value, v1 = +z.value; if (v0 > v1) [v0, v1] = [v1, v0]; st.y0 = v0; st.y1 = v1; filt(); };
    a.addEventListener('input', upd); z.addEventListener('input', upd);
    let timer = null; const play = document.getElementById('play');
    play.addEventListener('click', () => { if (timer) { clearInterval(timer); timer = null; play.textContent = '▶'; return; } play.textContent = '❚❚';
      let y = 1000; timer = setInterval(() => { y += 25; if (y > 2026) y = 1000; a.value = y - 50; z.value = y; upd(); }, 700); });
    if (qs.get('from')) a.value = +qs.get('from'); if (qs.get('to')) z.value = +qs.get('to');
    upd();
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idxs = P.rows.map((r, i) => ({ n: r[1], nn: norm(r[1]), i, s: dtxt(r[4], r[5], r[6]), sl: r[11] }));
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      const strip = s => s.replace(/^(battle|siege|capture|attack) (of|on) (the )?/, '');
      items = idxs.filter(x => strip(x.nn).startsWith(v) || x.nn.startsWith(v)).concat(idxs.filter(x => !(strip(x.nn).startsWith(v) || x.nn.startsWith(v)) && v.length > 3 && x.nn.includes(v)))
        .sort((a, b) => b.sl - a.sl).slice(0, 12);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.n)} <span>${esc(it.s)}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.n; sug.style.display = 'none'; fold(true);
      const r = P.rows[it.i]; if (r[4] < st.y0 || r[4] > st.y1) { document.getElementById('ya').value = -600; document.getElementById('yz').value = 2026; st.y0 = -600; st.y1 = 2026; filt(); }
      map.flyTo({ center: [r[2], r[3]], zoom: 8, duration: 1400 }); map.once('moveend', () => popup(it.i, [r[2], r[3]])); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
    document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const qq = a.dataset.go; const i = P.rows.findIndex(r => r[0] === qq); if (i < 0) return;
      document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); const r = P.rows[i]; map.flyTo({ center: [r[2], r[3]], zoom: 7, duration: 1400 }); map.once('moveend', () => popup(i, [r[2], r[3]])); }));
  }
  Promise.all([fetch('data/points.json').then(r => r.json()), fetch('data/site.json').then(r => r.json())]).then(([p, s]) => {
    P = p; S = s;
    const at = (qs.get('at') || '').split(',').map(Number);
    const mo = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { center: small ? [12, 45] : [14, 44], zoom: small ? 2.3 : 3.1 };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 15, renderWorldCopies: false }, mo));
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    setup(); setupSearch();
    document.getElementById('mapWrap').addEventListener('pointerdown', e => { if (e.target.closest && e.target.closest('.cartouche,.ov,.lp,.tl,.wheel,.mfs-btn,.maplibregl-ctrl')) return; fold(true); }, { capture: true, passive: true, once: true });
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
