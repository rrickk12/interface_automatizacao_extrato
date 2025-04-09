import { exposeToWindow } from './expose.js';
import { initApp } from './init.js'; // agora funciona porque init exporta

console.log("✅ main.js carregado");

window.eval = () => {
  console.error("⚠️ Tentativa de uso de eval bloqueada por CSP.");
  return null;
};

exposeToWindow();
console.log(window.carregarRegrasConfig, window.aplicarRegras, window.carregarRegras);
document.addEventListener('DOMContentLoaded', () => {
  initApp(); // <-- só chama depois que expose já rodou
});

document.addEventListener('click', (e) => {
  const btn = e.target.closest('.status-btn');
  if (btn) {
    const status = btn.dataset.status;
    if (status && typeof window.setStatus === 'function') {
      window.setStatus(btn, status);
    }
  }
});

document.addEventListener('change', (e) => {
  const tipoSelect = e.target.closest('select[name="categoria_tipo"]');
  if (tipoSelect && typeof window.atualizarCategorias === 'function') {
    window.atualizarCategorias(tipoSelect);
  }
});
