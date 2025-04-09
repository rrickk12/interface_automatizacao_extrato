async function esperarTransacoesCarregadas(selector = '#aba-transacoes tbody tr.pending', tentativas = 10, intervalo = 200) {
  return new Promise((resolve) => {
    const checar = () => {
      const rows = document.querySelectorAll(selector);
      if (rows.length > 0) {
        console.log(`✅ ${rows.length} transações encontradas`);
        resolve(rows);
      } else if (tentativas-- > 0) {
        setTimeout(checar, intervalo);
      } else {
        console.warn(`⚠️ Nenhuma transação encontrada após várias tentativas (${selector})`);
        resolve([]); // <- Não rejeita, apenas segue
      }
    };
    checar();
  });
}

export async function initApp() {
  console.log("🧪 init.js -> Inicialização do sistema...");

  try {
    // 🧩 1. Configuração inicial embutida no HTML
    console.log("📦 Lendo configurações embutidas...");
    const configData = document.getElementById("app-config");
    window.config_json = JSON.parse(configData?.dataset.config || "{}");
    window.regras_json = JSON.parse(configData?.dataset.regras || "[]");
    window.configCategorias = window.config_json;

    // 📥 2. Carregar regras do servidor (sobrepõe as embutidas)
    console.log("🔃 Buscando regras do servidor...");
    const regras = await window.carregarRegrasConfig();
    window.regras = regras;
    window.carregarRegras(regras, "#tabela-regras tbody");

    // 👥 3. Carregar contatos e exibir
    console.log("📇 Carregando contatos...");
    await window.loadContacts();
    window.renderContacts();

    // ⏳ 4. Esperar transações aparecerem no DOM
    console.log("⌛ Esperando transações no DOM...");
    await esperarTransacoesCarregadas();

    // 🔍 5. Aplicar tipos e regras automaticamente
    console.log("✨ Aplicando regras e tipos nas transações...");
    document.querySelectorAll('#aba-transacoes tbody tr.pending').forEach(row => {
      window.atualizarTipos(row);
      window.aplicarRegras(row);
    });

    // 📝 6. Formulário de contatos
    console.log("🧩 Iniciando formulário de contatos...");
    window.setupFormListener();

    // 🧭 7. Alternância entre abas
    console.log("🧭 Ligando troca de abas...");
    document.querySelectorAll('button[data-aba]').forEach(button => {
      button.addEventListener('click', () => {
        const aba = button.getAttribute('data-aba');
        console.log(`🔀 Alternando para aba: ${aba}`);
        window.abrirAba(aba);
      });
    });
    window.abrirAba('transacoes');

    // 🕹️ 8. Mapeamento de botões de ação
    console.log("🕹️ Mapeando botões...");
    [
      ['btn-save-state', window.saveState],
      ['btn-load-state', window.loadState],
      ['btn-clean-state', window.cleanState],
      ['btn-undo', window.undo],
      ['btn-redo', window.redo],
      ['btn-export-state', window.exportState],
      ['btn-import-state', () => document.getElementById('import-state-input')?.click()],
      ['btn-export-csv', window.exportToCSV],
      ['btn-upload-html', (e) => window.uploadHTML(e)],
      ['btn-run-pipeline', window.runPipeline],
      ['btn-add-contact', window.showAddContactForm],
      ['btn-cancel-contact', window.hideAddContactForm],
      ['btn-export-contacts', window.exportContacts],
      ['btn-import-contacts', () => document.getElementById('import-contacts-input')?.click()],
      ['btn-save-rules', window.saveRules],
      ['btn-load-rules', window.loadRules],
      ['btn-clean-rules', window.cleanRules],
      ['btn-export-rules', window.exportRules],
      ['btn-import-rules', () => document.getElementById('import-rules-input')?.click()],
      ['btn-add-rule', window.adicionarRegra]
    ].forEach(([id, handler]) => {
      const el = document.getElementById(id);
      if (el) el.addEventListener('click', handler);
    });

    // 📂 9. Inputs para importar arquivos
    document.getElementById('import-state-input')?.addEventListener('change', window.importState);
    document.getElementById('import-contacts-input')?.addEventListener('change', window.importContacts);

    // 💾 10. Auto salvar mudanças nas transações
    document.addEventListener('change', e => {
      if (e.target.closest('#aba-transacoes tbody')) {
        window.saveState();
      }
    });

    // 📝 11. Auto salvar ao editar regras
    const tabelaRegras = document.getElementById('tabela-regras');
    if (tabelaRegras) {
      tabelaRegras.addEventListener('input', () => window.saveRules());
    }

    // 🎉 Conclusão
    console.log("✅ App inicializado com sucesso!");
  } catch (err) {
    console.error("❌ Erro na inicialização:", err);
  }
}
document.getElementById("btn-run-pipeline").disabled = true;
