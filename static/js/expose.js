// static/js/expose.js
import {
    runPipeline, uploadHTML
  } from './pipeline/index.js';
  import {
    captureState, applyState, saveStateToServer, loadStateFromServer,
    cleanStateOnServer, pushStateToUndo, undo, redo, importStateFromFile
  } from './state/index.js';
  import {
    atualizarTipos, atualizarCategorias, aplicarRegras,
    criarRegra, carregarRegras, removerRegra, carregarRegrasConfig
  } from './rules/index.js';
  import {
    saveRulesToServer, loadRulesFromServer, cleanRulesOnServer
  } from './rules_state/index.js';
  import {
    showAddContactForm, hideAddContactForm, setupFormListener,
    renderContacts, removeContact, updateContact,
    exportContacts, importContacts, loadContacts, saveContacts
  } from './contacts/index.js';
  import * as debug from './debug.js';
  
  function setStatus(button, status) {
    const row = button.closest("tr");
    row.classList.remove("validated", "canceled", "pending");
    row.classList.add(status);
  }
  
  function exportToCSV() {
    const rows = document.querySelectorAll('#aba-transacoes tbody tr');
    let csv = 'Data,Descrição,Valor,Tipo Transação,Documento,Contato,Tipo,Categoria,Memo,Status\n';
  
    rows.forEach(row => {
      const cols = row.querySelectorAll('td');
      const getVal = td => td.querySelector('input')?.value?.trim() || td.innerText.trim();
      const vals = [
        getVal(cols[0]), getVal(cols[1]), getVal(cols[2]),
        getVal(cols[3]), getVal(cols[4]), getVal(cols[5]),
        row.querySelector('select[name="categoria_tipo"]')?.value || '',
        row.querySelector('select[name="categoria_nome"]')?.value || '',
        row.querySelector('input[name="memo"]')?.value || '',
        row.className || ''
      ];
      csv += vals.map(v => `"${v.replace(/"/g, '""')}"`).join(',') + '\n';
    });
  
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = Object.assign(document.createElement("a"), {
      href: URL.createObjectURL(blob),
      download: 'relatorio_transacoes.csv'
    });
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  
  function abrirAba(qual) {
    document.querySelectorAll('.aba').forEach(el => el.classList.remove('visible'));
    const target = document.getElementById('aba-' + qual);
    if (target) target.classList.add('visible');
  }
  
  export function exposeToWindow() {
    console.log("🔧 expose.js -> Registrando funções no window...");
  
    Object.assign(window, {
      setupFormListener, carregarRegrasConfig,
      runPipeline, uploadHTML,
      captureState, applyState, undo, redo,
      showAddContactForm, hideAddContactForm, renderContacts, removeContact,
      updateContact, exportContacts, importContacts, loadContacts, saveContacts,
      abrirAba,
      setStatus,
      exportToCSV,
      atualizarTipos: row => atualizarTipos(row, window.configCategorias),
      atualizarCategorias: el => atualizarCategorias(el, window.configCategorias),
      aplicarRegras: row => {
        if (!row.classList.contains('pending')) return;
        row.classList.remove('auto-classificado');
        aplicarRegras(row, window.regras);
      },
      exportState() {
        console.log("⬇️ Exportando estado");
        const blob = new Blob([JSON.stringify(captureState(), null, 2)], { type: "application/json" });
        const url = URL.createObjectURL(blob);
        const a = Object.assign(document.createElement("a"), {
          href: url,
          download: "estado_transacoes.json"
        });
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      },
      importState(event) {
        console.log("⬆️ Importando estado de arquivo...");
        const file = event.target.files[0];
        if (!file) return;
        importStateFromFile(file)
          .then(applyState)
          .catch(err => debug.error("Erro ao importar estado:", err));
      },
      saveState() {
        console.log("💾 Salvando estado...");
        const state = captureState();
        saveStateToServer(state)
          .then(() => pushStateToUndo())
          .catch(err => debug.error("Erro ao salvar estado:", err));
      },
      loadState() {
        console.log("📂 Carregando estado...");
        loadStateFromServer()
          .then(applyState)
          .catch(err => debug.error("Erro ao carregar estado:", err));
      },
      cleanState() {
        console.log("🧹 Limpando estado...");
        document.querySelectorAll("#aba-transacoes tbody tr").forEach(row => {
          row.querySelector('select[name="categoria_tipo"]').value = "";
          row.querySelector('select[name="categoria_nome"]').innerHTML = '<option value="">Selecione</option>';
          row.className = "pending";
        });
        cleanStateOnServer()
          .then(() => alert("Estado limpo"))
          .catch(err => debug.error("Erro ao limpar estado:", err));
      },
      adicionarRegra() {
        console.log("➕ Adicionando regra...");
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
        console.log("❌ Removendo regra índice:", index);
        window.regras = removerRegra(window.regras, index);
        carregarRegras(window.regras, "#tabela-regras tbody");
        document.querySelectorAll('#aba-transacoes tbody tr').forEach(window.aplicarRegras);
        window.saveRules();
      },
      saveRules: () => {
        console.log("💾 Salvando regras...");
        return saveRulesToServer(window.regras).catch(debug.error);
      },
      loadRules() {
        console.log("📂 Carregando regras...");
        loadRulesFromServer()
          .then(rules => {
            window.regras = rules;
            carregarRegras(window.regras, "#tabela-regras tbody");
          })
          .catch(err => debug.error("Erro ao carregar regras:", err));
      },
      cleanRules() {
        console.log("🧹 Limpando regras...");
        window.regras = [];
        carregarRegras([], "#tabela-regras tbody");
        cleanRulesOnServer().catch(debug.error);
      },
      exportRules() {
        console.log("⬇️ Exportando regras...");
        const blob = new Blob([JSON.stringify(window.regras, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = Object.assign(document.createElement("a"), {
          href: url,
          download: "rules_state.json"
        });
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      },
      updateRegra(index, field, value) {
        console.log(`✏️ Atualizando regra #${index} campo ${field}:`, value);
        if (!window.regras?.[index]) return;
        window.regras[index][field] = field === 'descricao_contain'
          ? value.split(',').map(v => v.trim()).filter(Boolean)
          : value.trim();
  
        document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => {
          row.classList.remove('auto-classificado');
          aplicarRegras(row, window.regras);
        });
  
        window.saveRules();
      }
    });
  
    console.log("✅ Funções registradas no window:", Object.keys(window).filter(k => typeof window[k] === 'function'));
  }