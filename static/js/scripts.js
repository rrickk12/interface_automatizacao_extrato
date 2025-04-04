(function() {
      // Variáveis globais vindas do Flask (definidas via template)
  const configCategorias = window.configCategorias || {};
  let regras = window.regras || [];

  // Função para trocar de aba (transações ou regras)
  window.abrirAba = function(qual) {
    document.getElementById('aba-transacoes').classList.remove('visible');
    document.getElementById('aba-regras').classList.remove('visible');
    document.getElementById('aba-' + qual).classList.add('visible');
  };

  // Função para executar o pipeline via requisição POST
  window.runPipeline = function() {
    // Opcional: exibir um status para o usuário
    const statusDiv = document.getElementById('process-status');
    statusDiv.innerText = "Processando...";
    
    fetch('/process', {
      method: 'POST'
    })
    .then(response => {
      if (!response.ok) {
        throw new Error("Erro ao executar o pipeline.");
      }
      return response.json();
    })
    .then(data => {
      statusDiv.innerText = data.message;
      console.log("Pipeline executado com sucesso:", data);
      // Opcional: atualizar a interface ou recarregar dados
    })
    .catch(error => {
      statusDiv.innerText = "Falha: " + error.message;
      console.error("Erro:", error);
    });
  };

    // Função para capturar o estado atual da tabela
    function captureState() {
      let state = [];
      document.querySelectorAll("#aba-transacoes tbody tr").forEach(function(row) {
        let rowState = {
          tipo: row.querySelector('select[name="categoria_tipo"]').value,
          categoria: row.querySelector('select[name="categoria_nome"]').value,
          status: row.className
        };
        state.push(rowState);
      });
      return state;
    }
  
    // Função para aplicar um estado à tabela
    function applyState(state) {
      let rows = document.querySelectorAll("#aba-transacoes tbody tr");
      rows.forEach(function(row, index) {
        if (state[index]) {
          row.querySelector('select[name="categoria_tipo"]').value = state[index].tipo;
          window.atualizarCategorias(row.querySelector('select[name="categoria_tipo"]'));
          row.querySelector('select[name="categoria_nome"]').value = state[index].categoria;
          row.className = state[index].status;
        }
      });
    }
  
    // Salvar o estado atual no servidor
    window.saveState = function() {
      const state = captureState();
      fetch('/state/save', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(state)
      })
      .then(response => response.json())
      .then(data => {
        alert("State saved");
        // Registra o estado atual para undo
        pushStateToUndo();
      })
      .catch(err => console.error(err));
    };
  
    // Carregar o estado salvo do servidor e aplicar à tabela
    window.loadState = function() {
      fetch('/state/load')
        .then(response => {
          if (!response.ok) throw new Error("No state found");
          return response.json();
        })
        .then(state => {
          applyState(state);
          // alert("State loaded");
        })
        .catch(err => {
          // alert("Failed to load state: " + err.message);
          console.error(err);
        });
    };
  
    // Limpar o estado atual (resetar a tabela)
    window.cleanState = function() {
      document.querySelectorAll("#aba-transacoes tbody tr").forEach(function(row) {
        row.querySelector('select[name="categoria_tipo"]').value = "";
        row.querySelector('select[name="categoria_nome"]').innerHTML = '<option value="">Selecione</option>';
        row.className = "";
      });
      fetch('/state/clean', { method: "POST" })
        .then(response => response.json())
        // .then(data => alert("State cleaned"))
        .catch(err => console.error(err));
    };
  
    // Registrar o estado atual na pilha de undo
    function pushStateToUndo() {
      const state = captureState();
      undoStack.push(JSON.stringify(state));
      // Ao registrar uma nova ação, limpa a pilha redo
      redoStack = [];
    }
  
    // Função Undo: desfaz a última ação
    window.undo = function() {
      if (undoStack.length > 0) {
        // Salva o estado atual na pilha redo
        redoStack.push(JSON.stringify(captureState()));
        // Aplica o último estado da pilha de undo
        const prevState = JSON.parse(undoStack.pop());
        applyState(prevState);
      } else {
        // alert("No more undo actions available");
      }
    };
  
    // Função Redo: refaz a ação desfeita
    window.redo = function() {
      if (redoStack.length > 0) {
        // Salva o estado atual na pilha de undo
        undoStack.push(JSON.stringify(captureState()));
        const nextState = JSON.parse(redoStack.pop());
        applyState(nextState);
      } else {
        // alert("No more redo actions available");
      }
    };
  
    // Exporta o estado atual para um arquivo JSON para download
    window.exportState = function() {
      const state = captureState();
      const blob = new Blob([JSON.stringify(state, null, 2)], {type: "application/json"});
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "state.json";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };
  
    // Importa o estado a partir de um arquivo selecionado
    window.importState = function(event) {
      const file = event.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = function(e) {
        try {
          const state = JSON.parse(e.target.result);
          applyState(state);
          // alert("State imported successfully");
        } catch (err) {
          // alert("Failed to import state: " + err.message);
        }
      };
      reader.readAsText(file);
    };
  
    // Configura o listener para o input de importação
    document.getElementById("import-state-input").addEventListener("change", window.importState);
  
    // Atualiza o select de tipos baseado no tipo da transação
    window.atualizarTipos = function(row) {
      const tipoTransacao = row.dataset.tipoTransacao;
      const tipoSelect = row.querySelector('select[name="categoria_tipo"]');
      tipoSelect.innerHTML = '<option value="">Selecione</option>';
      if (configCategorias.tipos_por_transacao &&
          configCategorias.tipos_por_transacao[tipoTransacao]) {
        configCategorias.tipos_por_transacao[tipoTransacao].forEach(tipo => {
          tipoSelect.innerHTML += `<option value="${tipo}">${tipo}</option>`;
        });
      }
      // Reseta o select de categoria
      const categoriaSelect = row.querySelector('select[name="categoria_nome"]');
      if (categoriaSelect) {
        categoriaSelect.innerHTML = '<option value="">Selecione</option>';
      }
    };
  
    // Atualiza o select de categorias com base no tipo selecionado
    window.atualizarCategorias = function(selectElem) {
      const row = selectElem.closest('tr');
      const categoriaSelect = row.querySelector('select[name="categoria_nome"]');
      const tipoSelecionado = selectElem.value;
      categoriaSelect.innerHTML = '<option value="">Selecione</option>';
      const sugeridas = [];
      const outras = [];
  
      if (configCategorias.categorias_por_tipo) {
        Object.entries(configCategorias.categorias_por_tipo).forEach(([categoria, tipos]) => {
          if (tipos.includes(tipoSelecionado)) {
            sugeridas.push(categoria);
          } else {
            outras.push(categoria);
          }
        });
      }
  
      sugeridas.forEach(cat => {
        categoriaSelect.innerHTML += `<option value="${cat}">${cat}</option>`;
      });
  
      if (outras.length > 0) {
        categoriaSelect.innerHTML += '<option disabled>──────────────</option>';
      }
  
      outras.forEach(cat => {
        categoriaSelect.innerHTML += `<option value="${cat}">${cat}</option>`;
      });
    };
  
    // Define o status da linha (ex.: validated, canceled)
    window.setStatus = function(btn, status) {
      const row = btn.closest('tr');
      row.className = status;
    };
  
    // Exporta os dados da tabela para CSV
    window.exportToCSV = function() {
      let csv = 'Data,Descrição,Valor,Tipo Transação,Documento,Contato,Tipo,Categoria,Status\n';
      const rows = document.querySelectorAll('#aba-transacoes tbody tr');
      rows.forEach(row => {
        const cols = row.querySelectorAll('td');
        const tipo = row.querySelector('select[name="categoria_tipo"]').value || '';
        const categoria = row.querySelector('select[name="categoria_nome"]').value || '';
        const status = row.className || '';
        const values = [
          ...Array.from(cols).slice(0, 6).map(td => td.innerText.trim()),
          tipo,
          categoria,
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
  
    // Aplica as regras de classificação a uma linha da tabela
    window.aplicarRegras = function(row) {
      const desc = row.cells[1].innerText;
      const contato = row.cells[5].innerText;
      regras.forEach(regra => {
        let match = true;
        if (regra.descricao_contain && Array.isArray(regra.descricao_contain)) {
          match = regra.descricao_contain.every(p => desc.includes(p));
        }
        if (regra.descricao_regex && !(new RegExp(regra.descricao_regex).test(desc))) {
          match = false;
        }
        if (regra.contato_igual && regra.contato_igual !== contato) {
          match = false;
        }
        if (match) {
          const tipoSelect = row.querySelector('select[name="categoria_tipo"]');
          tipoSelect.value = regra.tipo;
          window.atualizarCategorias(tipoSelect);
          const categoriaSelect = row.querySelector('select[name="categoria_nome"]');
          categoriaSelect.value = regra.categoria;
          row.classList.add('auto-classificado');
        }
      });
    };
  
    // Adiciona uma nova regra a partir dos dados do formulário
    window.adicionarRegra = function() {
      const form = document.getElementById("form-regra");
      const novaRegra = {
        descricao_contain: form.descricao_contain.value.split(',').map(v => v.trim()).filter(Boolean),
        descricao_regex: form.descricao_regex.value.trim() || null,
        contato_igual: form.descricao_regex.value.trim() || null,
        tipo: form.tipo.value.trim(),
        categoria: form.categoria.value.trim()
      };
      regras.push(novaRegra);
      window.carregarRegras();
    };
  
    // Carrega as regras e as exibe na tabela de regras
    window.carregarRegras = function() {
      const corpo = document.querySelector("#tabela-regras tbody");
      if (!corpo) return;
      corpo.innerHTML = '';
      regras.forEach((regra, index) => {
        const linha = document.createElement('tr');
        linha.innerHTML = `
          <td>${(regra.descricao_contain || []).join(', ')}</td>
          <td>${regra.descricao_regex || ''}</td>
          <td>${regra.contato_igual || ''}</td>
          <td>${regra.tipo}</td>
          <td>${regra.categoria}</td>
          <td><button onclick="removerRegra(${index})">🗑️</button></td>
        `;
        corpo.appendChild(linha);
      });
      // Aplica as regras a todas as linhas de transações
      document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => window.aplicarRegras(row));
    };
  
    // Remove uma regra com base no índice
    window.removerRegra = function(index) {
      regras.splice(index, 1);
      window.carregarRegras();
    };
  
    // Inicialização ao carregar o DOM
    document.addEventListener('DOMContentLoaded', () => {
      window.abrirAba('transacoes');
      document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => window.atualizarTipos(row));
      window.carregarRegras();
    });
    document.addEventListener('DOMContentLoaded', () => {
      window.abrirAba('transacoes');
      document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => window.atualizarTipos(row));
      window.carregarRegras();
    });
  })();
  
  