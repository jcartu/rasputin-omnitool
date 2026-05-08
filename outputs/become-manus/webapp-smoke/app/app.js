document.getElementById('action').addEventListener('click', () => {
  document.getElementById('output').textContent = JSON.stringify({ok:true, capability:'webapp_smoke'}, null, 2);
});
