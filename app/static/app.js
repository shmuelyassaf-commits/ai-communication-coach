const area = document.querySelector('#answer');
if (area) {
  const start = Date.now(); let writingStart = null;
  const fmt = s => `${Math.floor(s/60)}:${String(s%60).padStart(2,'0')}`;
  area.addEventListener('input', () => {
    if (!writingStart) writingStart = Date.now();
    document.querySelector('#words').textContent = area.value.trim() ? area.value.trim().split(/\s+/).length : 0;
  });
  setInterval(() => {
    const now = Date.now();
    const thinking = Math.floor(((writingStart || now) - start) / 1000);
    const writing = writingStart ? Math.floor((now - writingStart) / 1000) : 0;
    document.querySelector('#thinking').value = thinking; document.querySelector('#writing').value = writing;
    document.querySelector('#think-clock').textContent = fmt(thinking); document.querySelector('#write-clock').textContent = fmt(writing);
  }, 1000);
}
