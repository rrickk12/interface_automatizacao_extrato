// main.js

import { runPipeline, uploadHTML } from './pipeline/index.js';
import {
  captureState, applyState, saveStateToServer, loadStateFromServer,
  cleanStateOnServer, pushStateToUndo, undo, redo,
  importStateFromFile
} from './state/index.js';
import {
  atualizarTipos, atualizarCategorias, aplicarRegras,
  criarRegra, carregarRegras, removerRegra, carregarRegrasConfig
} from './rules/index.js';
import {
  saveRulesToServer, loadRulesFromServer, cleanRulesOnServer
} from './rules_state/index.js';
import {
  showAddContactForm,
  hideAddContactForm,
  setupFormListener,
  renderContacts,
  removeContact,
  updateContact,
  exportContacts,
  importContacts,
  loadContacts,
  saveContacts
} from './contacts/index.js';

import * as debug from './debug.js';

window.debug = debug;
window.DEBUG_MODE = true;

// ------------------------------
// Debounce genérico
// ------------------------------
function debounce(func, delay) {
  let timeout;
  return (...args) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), delay);
  };
}

// ------------------------------
// Navegação entre abas
// ------------------------------
window.abrirAba = function (qual) {
  document.querySelectorAll('.aba').forEach(el => el.classList.remove('visible'));
  const target = document.getElementById('aba-' + qual);
  if (target) target.classList.add('visible');
};

// ------------------------------
// Estado (Transações)
// ------------------------------
Object.assign(window, {
  runPipeline,
  captureState,
  applyState,
  undo,
  redo,
  exportState() {
    const blob = new Blob([JSON.stringify(captureState(), null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "estado_transacoes.json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  },
  importState(event) {
    const file = event.target.files[0];
    if (!file) return;
    importStateFromFile(file)
      .then(state => applyState(state))
      .catch(err => debug.error("Erro ao importar estado:", err));
  },
  saveState() {
    const state = captureState();
    saveStateToServer(state)
      .then(() => pushStateToUndo())
      .catch(err => debug.error("Erro ao salvar estado:", err));
  },
  loadState() {
    loadStateFromServer()
      .then(state => applyState(state))
      .catch(err => debug.error("Erro ao carregar estado:", err));
  },
  cleanState() {
    document.querySelectorAll("#aba-transacoes tbody tr").forEach(row => {
      row.querySelector('select[name="categoria_tipo"]').value = "";
      row.querySelector('select[name="categoria_nome"]').innerHTML = '<option value="">Selecione</option>';
      row.className = "pending";
    });
    cleanStateOnServer()
      .then(() => alert("Estado limpo"))
      .catch(err => debug.error("Erro ao limpar estado:", err));
  }
});

// ------------------------------
// Regras
// ------------------------------
Object.assign(window, {
  atualizarTipos: row => atualizarTipos(row, window.configCategorias),
  atualizarCategorias: selectElem => atualizarCategorias(selectElem, window.configCategorias),
  aplicarRegras: row => {
    if (!row.classList.contains('pending')) return;
    row.classList.remove('auto-classificado');
    aplicarRegras(row, window.regras);
  },
  adicionarRegra() {
    const form = document.getElementById("form-regra");
    const novaRegra = criarRegra(form);
    window.regras = window.regras || [];
    window.regras.push(novaRegra);
    carregarRegras(window.regras, "#tabela-regras tbody");
    document.querySelectorAll('#aba-transacoes tbody tr').forEach(window.aplicarRegras);
    debug.log("Regra adicionada:", novaRegra);
    window.saveRules();
  },
  carregarRegras: () => carregarRegras(window.regras, "#tabela-regras tbody"),
  removerRule(index) {
    window.regras = removerRegra(window.regras, index);
    carregarRegras(window.regras, "#tabela-regras tbody");
    document.querySelectorAll('#aba-transacoes tbody tr').forEach(window.aplicarRegras);
    window.saveRules();
  },
  importRules(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
      try {
        window.regras = JSON.parse(e.target.result);
        carregarRegras(window.regras, "#tabela-regras tbody");
        alert("Regras importadas com sucesso");
        debug.log("Regras importadas:", window.regras);
      } catch (err) {
        alert("Erro ao importar regras: " + err.message);
        debug.error(err);
      }
    };
    reader.onerror = () => alert("Erro ao ler o arquivo");
    reader.readAsText(file);
  },
  saveRules: () => saveRulesToServer(window.regras).catch(err => debug.error(err)),
  loadRules() {
    loadRulesFromServer()
      .then(rules => {
        window.regras = rules;
        carregarRegras(window.regras, "#tabela-regras tbody");
      })
      .catch(err => debug.error("Erro ao carregar regras:", err));
  },
  cleanRules() {
    window.regras = [];
    carregarRegras([], "#tabela-regras tbody");
    cleanRulesOnServer().catch(err => debug.error(err));
  },
  exportRules() {
    const blob = new Blob([JSON.stringify(window.regras, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = Object.assign(document.createElement("a"), {
      href: url,
      download: "rules_state.json"
    });
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  },
  updateRegra(index, field, value) {
    if (!window.regras?.[index]) return;
    window.regras[index][field] =
      field === 'descricao_contain'
        ? value.split(',').map(v => v.trim()).filter(Boolean)
        : value.trim();

    document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => {
      row.classList.remove('auto-classificado');
      aplicarRegras(row, window.regras);
    });

    window.saveRules();
  }
});

// ------------------------------
// Contatos
// ------------------------------
Object.assign(window, {
  showAddContactForm,
  hideAddContactForm,
  renderContacts,
  removeContact,
  updateContact,
  exportContacts,
  importContacts,
  loadContacts,
  saveContacts
});

// ------------------------------
// Funções Auxiliares
// ------------------------------
window.setStatus = (button, status) => {
  const row = button.closest("tr");
  row.classList.remove("validated", "canceled", "pending");
  row.classList.add(status);
};

function getCellValue(td) {
  const input = td.querySelector('input');
  return input ? input.value.trim() : td.innerText.trim();
}

window.exportToCSV = function () {
  let csv = 'Data,Descrição,Valor,Tipo Transação,Documento,Contato,Tipo,Categoria,Memo,Status\n';
  const rows = document.querySelectorAll('#aba-transacoes tbody tr');
  rows.forEach(row => {
    const cols = row.querySelectorAll('td');
    const values = [
      getCellValue(cols[0]), getCellValue(cols[1]), getCellValue(cols[2]),
      getCellValue(cols[3]), getCellValue(cols[4]), getCellValue(cols[5]),
      row.querySelector('select[name="categoria_tipo"]').value || '',
      row.querySelector('select[name="categoria_nome"]').value || '',
      row.querySelector('input[name="memo"]')?.value || '',
      row.className || ''
    ];
    csv += values.map(v => `"${v.replace(/"/g, '""')}"`).join(',') + '\n';
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'relatorio_transacoes.csv';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

window.uploadHTML = uploadHTML;

// ------------------------------
// Carregamento Inicial
// ------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  window.abrirAba('transacoes');

  try {
    window.configCategorias = window.config_json || {};
    debug.log("Config carregada:", window.configCategorias);

    const regras = await carregarRegrasConfig();
    window.regras = regras;
    carregarRegras(regras, "#tabela-regras tbody");

    document.querySelectorAll('#aba-transacoes tbody tr.pending').forEach(row => {
      window.atualizarTipos(row);
      window.aplicarRegras(row);
    });

    // ⚠️ Novo: carregar contatos logo no início
    loadContacts();
    setupFormListener();

  } catch (err) {
    debug.error("Erro ao carregar configurações ou regras:", err);
  }

  const importInput = document.getElementById('import-rules-input');
  if (importInput) importInput.addEventListener('change', window.importRules);

  document.addEventListener('change', debounce(event => {
    if (event.target.closest('#aba-transacoes tbody')) {
      window.saveState();
    }
  }, 500));

  const tabelaRegras = document.getElementById('tabela-regras');
  if (tabelaRegras) {
    tabelaRegras.addEventListener('input', debounce(() => {
      window.saveRules();
    }, 500));
  }
});

// Fallback: caso updateReport não seja sobrescrito
if (!window.updateReport) {
  window.updateReport = () => location.reload();
}
