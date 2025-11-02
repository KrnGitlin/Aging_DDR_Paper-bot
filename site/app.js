async function load() {
  const res = await fetch('data/papers.json');
  const items = await res.json();
  return items;
}

function render(items) {
  const list = document.getElementById('list');
  list.innerHTML = '';
  for (const p of items) {
    const li = document.createElement('li');
    li.className = 'card';
    const date = new Date(p.published);
    const dateStr = date.toISOString().slice(0, 10);
    const authors = (p.authors || []).join(', ');
    const kw = (p.keywords_matched || []).map(k => `<span class="badge">${k.replace(/\\b/g, '')}</span>`).join(' ');
    li.innerHTML = `
      <div class="meta">
        <span class="badge">${p.source}</span>
        <span>${dateStr}</span>
      </div>
      <h3><a href="${p.link}" target="_blank" rel="noopener">${p.title}</a></h3>
      <div class="summary">${authors}</div>
      <div>${kw}</div>
    `;
    list.appendChild(li);
  }
}

function applyFilters(all) {
  const q = document.getElementById('search').value.trim().toLowerCase();
  const src = document.getElementById('source').value;
  let items = all;
  if (src) items = items.filter(p => p.source === src);
  if (q) items = items.filter(p => (p.title + '\n' + (p.summary||'')).toLowerCase().includes(q));
  render(items);
}

(async function() {
  const all = await load();
  render(all);
  document.getElementById('search').addEventListener('input', () => applyFilters(all));
  document.getElementById('source').addEventListener('change', () => applyFilters(all));
})();
