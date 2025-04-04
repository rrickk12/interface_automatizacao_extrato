// Função global para abrir abas (executada antes do DOM estar pronto)
window.abrirAba = function(qual) {
  const abas = document.querySelectorAll('.aba');
  if (!abas || abas.length === 0) {
    console.warn("Nenhuma aba encontrada no DOM.");
    return;
  }
  abas.forEach(el => el.classList.remove('visible'));
  const target = document.getElementById('aba-' + qual);
  if (target) {
    target.classList.add('visible');
  } else {
    console.warn("Elemento com id 'aba-" + qual + "' não foi encontrado.");
  }
};

// Função debounce simples
function debounce(func, delay) {
  let timeout;
  return function(...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), delay);
  };
}

// Importações dos módulos
import { runPipeline } from './pipeline.js';
import {
  captureState,
  applyState,
  saveStateToServer,
  loadStateFromServer,
  cleanStateOnServer,
  pushStateToUndo,
  undo,
  redo,
  exportStateToFile,
  importStateFromFile
} from './state.js';
import {
  atualizarTipos,
  atualizarCategorias,
  aplicarRegras,
  criarRegra,
  carregarRegras,
  removerRegra
} from './rules.js';
import {
  saveRulesToServer,
  loadRulesFromServer,
  cleanRulesOnServer
} from './rules_state.js';

// ------------------------------
// Funções de Estado (Transações)
// ------------------------------
window.runPipeline = runPipeline;
window.captureState = captureState;
window.applyState = applyState;

window.saveState = function() {
  const state = captureState();
  saveStateToServer(state)
    .then(data => {
      pushStateToUndo();
    })
    .catch(err => console.error(err));
};

window.loadState = function() {
  loadStateFromServer()
    .then(state => {
      applyState(state);
    })
    .catch(err => console.error(err));
};

window.cleanState = function() {
  document.querySelectorAll("#aba-transacoes tbody tr").forEach(function(row) {
    row.querySelector('select[name="categoria_tipo"]').value = "";
    row.querySelector('select[name="categoria_nome"]').innerHTML = '<option value="">Selecione</option>';
    // Define o estado padrão como "pending" para que as regras possam ser aplicadas
    row.className = "pending";
  });
  cleanStateOnServer()
    .then(data => alert("State cleaned"))
    .catch(err => console.error(err));
};

window.undo = undo;
window.redo = redo;
window.exportState = exportStateToFile;

window.importState = function(event) {
  const file = event.target.files[0];
  if (!file) return;
  importStateFromFile(file)
    .then(state => {
      applyState(state);
    })
    .catch(err => console.error(err));
};

// ------------------------------
// Funções de Regras
// ------------------------------
window.atualizarTipos = function(row) {
  atualizarTipos(row, window.configCategorias);
};

window.atualizarCategorias = function(selectElem) {
  atualizarCategorias(selectElem, window.configCategorias);
};

// Aplica regras somente se a linha estiver em "pending"
window.aplicarRegras = function(row) {
  if (!row.classList.contains('pending')) return;
  row.classList.remove('auto-classificado');
  aplicarRegras(row, window.regras);
};

window.adicionarRegra = function() {
  const form = document.getElementById("form-regra");
  const novaRegra = criarRegra(form);
  window.regras = window.regras || [];
  window.regras.push(novaRegra);
  carregarRegras(window.regras, "#tabela-regras tbody");

  // Reaplica regras apenas nas linhas pending
  document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => {
    window.aplicarRegras(row);
  });

  console.log("Regras atualizadas:", window.regras);
  window.saveRules();
};

window.carregarRegras = function() {
  carregarRegras(window.regras, "#tabela-regras tbody");
};

window.removerRule = function(index) {
  window.regras = removerRegra(window.regras, index);
  carregarRegras(window.regras, "#tabela-regras tbody");

  // Reaplica regras apenas nas linhas pending
  document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => {
    window.aplicarRegras(row);
  });
  window.saveRules();

};

window.importRules = function(event) {
  const file = event.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = function(e) {
    try {
      const importedRules = JSON.parse(e.target.result);
      window.regras = importedRules;
      carregarRegras(window.regras, "#tabela-regras tbody");
      alert("Regras importadas com sucesso");
    } catch (err) {
      alert("Falha ao importar regras: " + err.message);
      console.error(err);
    }
  };
  reader.onerror = () => alert("Erro ao ler o arquivo");
  reader.readAsText(file);
};

window.saveRules = function() {
  saveRulesToServer(window.regras)
    .catch(err => console.error(err));
};

window.loadRules = function() {
  loadRulesFromServer()
    .then(rulesState => {
      window.regras = rulesState;
      carregarRegras(window.regras, "#tabela-regras tbody");
    })
    .catch(err => console.error(err));
};

window.cleanRules = function() {
  window.regras = [];
  carregarRegras(window.regras, "#tabela-regras tbody");
  cleanRulesOnServer()
    .catch(err => console.error(err));
};

window.exportRules = function() {
  const blob = new Blob([JSON.stringify(window.regras, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "rules_state.json";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

// Função para atualizar o campo "Contato (parcial)" na regra editada
function updateRuleContato(index, value) {
  if (!window.regras || !window.regras[index]) return;
  window.regras[index].contato_igual = value;
  console.log("Atualizando regra " + index + " com novo contato:", value);
  // Opcional: salve automaticamente as regras após a alteração
  window.saveRules();
}

// ------------------------------
// Função para Upload de HTML
// ------------------------------
window.uploadHTML = function() {
  const input = document.getElementById("html-file-input");
  if (!input.files[0]) return;
  const formData = new FormData();
  formData.append("html_file", input.files[0]);
  
  fetch('/upload_html', {
    method: "POST",
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    // Processar a resposta, se necessário
  })
  .catch(err => {
    console.error(err);
  });
};

// ------------------------------
// Registro de Event Listeners
// ------------------------------
document.addEventListener('DOMContentLoaded', () => {
  // Abre a aba de transações e atualiza os tipos das linhas, se presentes
  if (document.getElementById('aba-transacoes')) {
    window.abrirAba('transacoes');
    document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => window.atualizarTipos(row));
  } else {
    console.warn("Elemento 'aba-transacoes' não encontrado.");
  }
  
  // Carrega as regras na tabela de regras
  if (document.getElementById('tabela-regras')) {
    carregarRegras(window.regras, "#tabela-regras tbody");
  }
  
  // Configura o input para importar regras
  const importRulesInput = document.getElementById('import-rules-input');
  if (importRulesInput) {
    importRulesInput.addEventListener('change', window.importRules);
  }
  
  // Cria a função debounced para salvar o estado das transações
  const debouncedSaveState = debounce(window.saveState, 500);
  
  // Listener para mudanças em inputs e selects na tabela de transações
  document.addEventListener('change', function(event) {
    if (event.target.matches('#aba-transacoes tbody tr select, #aba-transacoes tbody tr input')) {
      debouncedSaveState();
    }
  });
  
  // Listener para alterações na tabela de regras (salva regras com debounce)
  const tabelaRegras = document.getElementById('tabela-regras');
  if (tabelaRegras) {
    tabelaRegras.addEventListener('input', debounce(function(event) {
      window.saveRules();
    }, 500));
  }
});

window.setStatus = function(button, status) {
  const row = button.closest("tr");
  row.classList.remove("validated", "canceled", "pending");
  row.classList.add(status);
};

// ------------------------------
// Funções Auxiliares
// ------------------------------
function updateReport() {
  fetch('/data')
    .then(response => {
      if (!response.ok) throw new Error("Erro ao carregar dados do relatório.");
      return response.json();
    })
    .then(data => {
      const tbody = document.querySelector("#aba-transacoes tbody");
      tbody.innerHTML = ""; // Limpa o conteúdo existente
      
      data.forEach(item => {
        const tr = document.createElement("tr");
        tr.classList.add("pending");
        tr.setAttribute("data-tipo-transacao", item.transaction_type);
        
        tr.innerHTML = `
          <td>${item.date || ""}</td>
          <td>${item.description || ""}</td>
          <td>${item.amount || ""}</td>
          <td>${item.transaction_type || ""}</td>
          <td>${item.document || ""}</td>
          <td class="${(!item.contato || !item.contato.cpf_cnpj) ? "contato-alert" : ""}">
            ${item.contato ? item.contato.nome || "-" : "-"}
          </td>
          <td>
            <select name="categoria_tipo" onchange="atualizarCategorias(this)">
              <option value="">Selecione</option>
              ${window.configCategorias && window.configCategorias.tipos_por_transacao 
                ? Object.values(window.configCategorias.tipos_por_transacao)
                    .flat()
                    .map(tipo => `<option value="${tipo}">${tipo}</option>`)
                    .join("")
                : ""
              }
            </select>
          </td>
          <td>
            <select name="categoria_nome">
              <option value="">Selecione</option>
            </select>
          </td>
          <td>
            <button class="status-btn" onclick="setStatus(this, 'validated')">✅</button>
            <button class="status-btn" onclick="setStatus(this, 'canceled')">❌</button>
          </td>
        `;
        
        tbody.appendChild(tr);
        
        // Aplica as regras automaticamente (para linhas pending)
        window.aplicarRegras(tr);
      });
    })
    .catch(err => console.error(err));
}
function getCellValue(td) {
  const input = td.querySelector('input');
  return input ? input.value.trim() : td.innerText.trim();
}

window.exportToCSV = function() {
  let csv = 'Data,Descrição,Valor,Tipo Transação,Documento,Contato,Tipo,Categoria,Memo,Status\n';
  const rows = document.querySelectorAll('#aba-transacoes tbody tr');
  rows.forEach(row => {
    const cols = row.querySelectorAll('td');
    // Use getCellValue para pegar o valor atualizado da célula, inclusive se contiver input
    const values = [
      getCellValue(cols[0]),
      getCellValue(cols[1]),
      getCellValue(cols[2]),
      getCellValue(cols[3]),
      getCellValue(cols[4]),
      getCellValue(cols[5]),
      row.querySelector('select[name="categoria_tipo"]').value || '',
      row.querySelector('select[name="categoria_nome"]').value || '',
      row.querySelector('input[name="memo"]') ? row.querySelector('input[name="memo"]').value : '',
      row.className || ''
    ];
    csv += values.map(v => `"${v.replace(/"/g, '""')}"`).join(',') + '\n';
  });
  
  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', 'relatorio_transacoes.csv');
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};