import { abrirAba } from './ui/abas.js';
import { carregarConfigERegras } from './config.js';
import { aplicarRegrasEmPendentes } from './rules/index.js';
import { debounce } from './utils/debounce.js';
import { saveState } from './state/server.js';

export function initApp() {
  window.abrirAba = abrirAba;
  abrirAba('transacoes');

  carregarConfigERegras().then(() => {
    document.querySelectorAll('#aba-transacoes tbody tr.pending').forEach(row => {
      aplicarRegrasEmPendentes(row);
    });
  });

  // Auto-save
  const debouncedSave = debounce(() => saveState(), 500);
  document.addEventListener('change', e => {
    if (e.target.closest('#aba-transacoes tbody')) debouncedSave();
  });
}
