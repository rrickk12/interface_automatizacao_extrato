import { aplicarRegras } from './apply.js';

export function exposeUpdateInline() {
  window.updateRegra = function(index, field, value) {
    if (!window.regras || !window.regras[index]) return;

    if (field === 'descricao_contain') {
      window.regras[index][field] = value.split(',').map(v => v.trim()).filter(Boolean);
    } else {
      window.regras[index][field] = value.trim();
    }

    console.debug("Regra atualizada:", window.regras[index]);

    document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => {
      row.classList.remove('auto-classificado');
      aplicarRegras(row, window.regras);
    });

    if (typeof window.saveRules === 'function') window.saveRules();
  };
}
