// Defina imediatamente a função global para abrir abas, 
// mas certifique-se de não chamá-la antes que o DOM esteja pronto.
window.abrirAba = function(qual) {
  // Tenta obter todas as abas; se nenhuma for encontrada, avisa
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



// Expor funções para o pipeline e para o gerenciamento de estado da tabela
window.runPipeline = runPipeline;
window.captureState = captureState;
window.applyState = applyState;
window.saveState = function() {
  const state = captureState();
  saveStateToServer(state)
    .then(data => {
      alert("State saved");
      pushStateToUndo();
    })
    .catch(err => console.error(err));
};
window.loadState = function() {
  loadStateFromServer()
    .then(state => {
      applyState(state);
      alert("State loaded");
    })
    .catch(err => {
      alert("Failed to load state: " + err.message);
      console.error(err);
    });
};
window.cleanState = function() {
  document.querySelectorAll("#aba-transacoes tbody tr").forEach(function(row) {
    row.querySelector('select[name="categoria_tipo"]').value = "";
    row.querySelector('select[name="categoria_nome"]').innerHTML = '<option value="">Selecione</option>';
    row.className = "";
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
      alert("State imported successfully");
    })
    .catch(err => {
      alert("Failed to import state: " + err.message);
      console.error(err);
    });
};

// Expor funções de regras para o gerenciamento de regras
window.atualizarTipos = function(row) {
  atualizarTipos(row, window.configCategorias);
};
window.atualizarCategorias = function(selectElem) {
  atualizarCategorias(selectElem, window.configCategorias);
};
window.aplicarRegras = function(row) {
  row.classList.remove('auto-classificado');
  aplicarRegras(row, window.regras);
};
window.adicionarRegra = function() {
  const form = document.getElementById("form-regra");
  const novaRegra = criarRegra(form);
  window.regras.push(novaRegra);
  carregarRegras(window.regras, "#tabela-regras tbody");

  // 🔁 Reaplica regras em todas as linhas da tabela
  document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => {
    window.aplicarRegras(row);
  });
};
window.carregarRegras = function() {
  carregarRegras(window.regras, "#tabela-regras tbody");
};
window.removerRule = function(index) {
  window.regras = removerRegra(window.regras, index);
  carregarRegras(window.regras, "#tabela-regras tbody");

  // 🔁 Reaplica regras em todas as linhas
  document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => {
    window.aplicarRegras(row);
  });
};


// Expor funções para gerenciamento do estado das regras
window.saveRules = function() {
  saveRulesToServer(window.regras)
    .then(() => alert("Rules state saved"))
    .catch(err => console.error(err));
};
window.loadRules = function() {
  loadRulesFromServer()
    .then(rulesState => {
      window.regras = rulesState;
      carregarRegras(window.regras, "#tabela-regras tbody");
      alert("Rules state loaded");
    })
    .catch(err => {
      alert("Failed to load rules: " + err.message);
      console.error(err);
    });
};
window.cleanRules = function() {
  window.regras = [];
  carregarRegras(window.regras, "#tabela-regras tbody");
  cleanRulesOnServer()
    .then(() => alert("Rules state cleaned"))
    .catch(err => console.error(err));
};
window.exportRules = function() {
  const blob = new Blob([JSON.stringify(window.regras, null, 2)], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "rules_state.json";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

window.uploadHTML = function() {
  const input = document.getElementById("html-file-input");
  if (!input.files[0]) {
    alert("Selecione um arquivo HTML.");
    return;
  }
  const formData = new FormData();
  formData.append("html_file", input.files[0]);
  
  fetch('/upload_html', {
    method: "POST",
    body: formData
  })
  .then(response => response.json())
  .then(data => {
    alert(data.message);
  })
  .catch(err => {
    console.error(err);
    alert("Erro ao carregar o arquivo HTML.");
  });
};


// Inicialização da interface, somente se os elementos existirem
document.addEventListener('DOMContentLoaded', () => {
  if (document.getElementById('aba-transacoes')) {
    window.abrirAba('transacoes');
    document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => window.atualizarTipos(row));
  } else {
    console.warn("Elemento 'aba-transacoes' não encontrado.");
  }
  if (document.getElementById('tabela-regras')) {
    carregarRegras(window.regras, "#tabela-regras tbody");
  }
});

window.setStatus = function(button, status) {
  const row = button.closest("tr");
  row.classList.remove("validated", "canceled", "pending");
  row.classList.add(status);
};

function updateReport() {
  fetch('/data')
    .then(response => {
      if (!response.ok) throw new Error("Erro ao carregar dados do relatório.");
      return response.json();
    })
    .then(data => {
      const tbody = document.querySelector("#aba-transacoes tbody");
      tbody.innerHTML = ""; // limpa tudo

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

        // ⬇️ Adiciona ao DOM
        tbody.appendChild(tr);

        // ⬇️ APLICA TUDO DEPOIS DE INSERIR
        if (window.atualizarTipos) window.atualizarTipos(tr);
        if (window.aplicarRegras) window.aplicarRegras(tr);
      });
    })
    .catch(err => console.error(err));
}

window.exportToCSV = function() {
  // Atualize o cabeçalho para incluir o campo Memo
  let csv = 'Data,Descrição,Valor,Tipo Transação,Documento,Contato,Tipo,Categoria,Memo,Status\n';
  const rows = document.querySelectorAll('#aba-transacoes tbody tr');
  rows.forEach(row => {
    // Seleciona as 6 primeiras células (Data, Descrição, Valor, Tipo Transação, Documento, Contato)
    const cols = row.querySelectorAll('td');
    // Busca os selects e input do memo
    const tipo = row.querySelector('select[name="categoria_tipo"]').value || '';
    const categoria = row.querySelector('select[name="categoria_nome"]').value || '';
    const memo = row.querySelector('input[name="memo"]').value || '';
    // Você está usando o nome da classe da linha para indicar status (por exemplo, "pending", "validated", etc.)
    const status = row.className || '';
    
    // Constrói o array de valores na ordem das colunas do cabeçalho:
    const values = [
      ...Array.from(cols).slice(0, 6).map(td => td.innerText.trim()),
      tipo,
      categoria,
      memo,
      status
    ];
    csv += values.map(v => `"${v.replace(/"/g, '""')}"`).join(',') + '\n';
  });

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', 'relatorio_transacoes.csv');
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};