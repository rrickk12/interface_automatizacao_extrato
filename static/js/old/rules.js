// static/js/rules.js

/**
 * Atualiza o select de "Tipo" (categoria_tipo) com base no tipo da transação.
 * Usa a configuração armazenada em configCategorias.
 * @param {HTMLElement} row - A linha da transação (tr).
 * @param {Object} configCategorias - Objeto com as configurações dos tipos e categorias.
 */
export function atualizarTipos(row, configCategorias) {
  const tipoTransacao = row.dataset.tipoTransacao || "Indefinido";
  const tipoSelect = row.querySelector('select[name="categoria_tipo"]');
  if (tipoSelect) {
    tipoSelect.innerHTML = '<option value="">Selecione</option>';
    if (configCategorias.tipos_por_transacao && configCategorias.tipos_por_transacao[tipoTransacao]) {
      configCategorias.tipos_por_transacao[tipoTransacao].forEach(tipo => {
        tipoSelect.innerHTML += `<option value="${tipo}">${tipo}</option>`;
      });
    }
  }
  const categoriaSelect = row.querySelector('select[name="categoria_nome"]');
  if (categoriaSelect) {
    categoriaSelect.innerHTML = '<option value="">Selecione</option>';
  }
}

/**
 * Atualiza o select de "Categoria" (categoria_nome) com base no tipo selecionado.
 * Utiliza as configurações definidas em configCategorias.
 * @param {HTMLElement} selectElem - O select do campo "tipo" que foi alterado.
 * @param {Object} configCategorias - Objeto com as configurações.
 */
export function atualizarCategorias(selectElem, configCategorias) {
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
  // Adiciona as categorias sugeridas
  sugeridas.forEach(cat => {
    categoriaSelect.innerHTML += `<option value="${cat}">${cat}</option>`;
  });
  if (outras.length > 0) {
    categoriaSelect.innerHTML += '<option disabled>──────────────</option>';
  }
  outras.forEach(cat => {
    categoriaSelect.innerHTML += `<option value="${cat}">${cat}</option>`;
  });
}

/**
 * Percorre as regras para verificar se a transação (linha) deve ser automaticamente modificada.
 * Se os critérios forem atendidos, atualiza os selects de "Tipo" e "Categoria", o input de "Memo",
 * e, se necessário, o campo de contato.
 *
 * @param {HTMLElement} row - Linha (tr) da transação.
 * @param {Array} regras - Array de regras a serem aplicadas.
 */
export function aplicarRegras(row, regras) {
  // Pega a descrição (assumindo que a coluna 2 contém a descrição)
  const desc = row.cells[1] ? row.cells[1].innerText : "";
  // Obtém o valor do campo "Contato" de forma inline (ou usa a célula, se não houver input)
  const contatoElem = row.querySelector('input[name="contato_parcial"]');
  const contato = contatoElem ? contatoElem.value : (row.cells[5] ? row.cells[5].innerText : "");

  // Obtém o tipo da transação a partir de um data attribute (ou usa "Indefinido")
  const transacaoTipo = row.dataset.tipoTransacao || "Indefinido";

  regras.forEach(regra => {
    let match = true;

    // 1. Critério: "Descrição Contém"
    if (regra.descricao_contain && Array.isArray(regra.descricao_contain)) {
      match = regra.descricao_contain.every(palavra => desc.includes(palavra));
    }

    // // 2. Critério: Regex (se definido)
    // if (match && regra.descricao_regex) {
    //   try {
    //     const re = new RegExp(regra.descricao_regex);
    //     if (!re.test(desc)) {
    //       match = false;
    //     }
    //   } catch (e) {
    //     console.error("Regex inválida:", regra.descricao_regex, e);
    //     match = false;
    //   }
    // }

    // 3. Critério: Contato (deve ser igual, ou conter a string definida)
    if (match && regra.contato_igual) {
      if (!contato || !contato.includes(regra.contato_igual)) {
        match = false;
      }
    }

    // 4. Critério: Tipo de Transação
    if (match && regra.transaction_type && regra.transaction_type !== "Indefinido") {
      if (regra.transaction_type.toLowerCase() !== transacaoTipo.toLowerCase()) {
        match = false;
      }
    }

    // Se todos os critérios foram atendidos, atualiza os campos da linha
    if (match) {
      // Atualiza o select de "Tipo" (categoria_tipo) conforme a regra
      const tipoSelect = row.querySelector('select[name="categoria_tipo"]');
      if (tipoSelect) {
        tipoSelect.value = regra.tipo;
        atualizarCategorias(tipoSelect, window.configCategorias);
      }
      // Atualiza o select de "Categoria"
      const categoriaSelect = row.querySelector('select[name="categoria_nome"]');
      if (categoriaSelect) {
        categoriaSelect.value = regra.categoria;
      }
      // Atualiza o input de "Memo"
      const memoInput = row.querySelector('input[name="memo"]');
      if (memoInput) {
        memoInput.value = regra.memo_rule || "";
      }
      // Atualiza o campo de contato, se desejado (opcional)
      const contatoInput = row.querySelector('input[name="contato_parcial"]');
      if (contatoInput && regra.contato_igual) {
        contatoInput.value = regra.contato_igual;
      }
      row.classList.add('auto-classificado');
    }
  });
}

/**
 * Cria um objeto regra a partir do formulário (SEM regex).
 */
export function criarRegra(form) {
  return {
    // Divide a string de descrição_contain em array
    descricao_contain: form.descricao_contain.value.split(',')
      .map(str => str.trim())
      .filter(Boolean),

    // Tipo de Transação (Crédito, Débito, Indefinido)
    transaction_type: form.transaction_type.value.trim() || "Indefinido",

    // Contato parcial
    contato_igual: form.contato_igual.value.trim() || null,

    // Tipo (ex.: Recebimentos, Transferência)
    tipo: form.tipo.value.trim(),

    // Categoria
    categoria: form.categoria.value.trim(),

    // Memo
    memo_rule: form.memo_rule.value.trim() || null
  };
}

/**
 * Renderiza as regras em uma tabela, sem a coluna Regex.
 * @param {Array} regras - Array de objetos de regra.
 * @param {String} tableBodySelector - Seletor para o <tbody> da tabela.
 */
export function carregarRegras(regras, tableBodySelector) {
  const corpo = document.querySelector(tableBodySelector);
  if (!corpo) return;
  corpo.innerHTML = '';

  regras.forEach((regra, index) => {
    const linha = document.createElement('tr');
    linha.innerHTML = `
      <!-- Descrição Contém -->
      <td>
        <input type="text" 
               name="descricao_contain" 
               value="${(regra.descricao_contain || []).join(', ')}"
               onchange="updateRegra(${index}, 'descricao_contain', this.value)">
      </td>

      <!-- Tipo de Transação -->
      <td>
        <select name="transaction_type" onchange="updateRegra(${index}, 'transaction_type', this.value)">
          <option value="Indefinido" ${regra.transaction_type==='Indefinido' ? 'selected' : ''}>Indefinido</option>
          <option value="Crédito" ${regra.transaction_type==='Crédito' ? 'selected' : ''}>Crédito</option>
          <option value="Débito" ${regra.transaction_type==='Débito' ? 'selected' : ''}>Débito</option>
        </select>
      </td>

      <!-- Contato (parcial) -->
      <td>
        <input type="text" 
               name="contato_igual" 
               value="${regra.contato_igual || ''}" 
               onchange="updateRegra(${index}, 'contato_igual', this.value)">
      </td>

      <!-- Tipo (Ex.: Recebimentos, Transferência) -->
      <td>
        <select name="tipo" onchange="updateRegra(${index}, 'tipo', this.value)">
          <option value="" ${!regra.tipo ? 'selected' : ''}>Selecione o Tipo</option>
          <option value="Recebimentos" ${regra.tipo==='Recebimentos' ? 'selected' : ''}>Recebimentos</option>
          <option value="Transferência" ${regra.tipo==='Transferência' ? 'selected' : ''}>Transferência</option>
        </select>
      </td>

      <!-- Categoria -->
      <td>
        <select name="categoria" onchange="updateRegra(${index}, 'categoria', this.value)">
          <option value="" ${!regra.categoria ? 'selected' : ''}>Selecione a Categoria</option>
          <option value="Locação de equipamentos" ${regra.categoria==='Locação de equipamentos' ? 'selected' : ''}>Locação de equipamentos</option>
          <!-- Outras opções, se desejar -->
        </select>
      </td>

      <!-- Memo -->
      <td>
        <input type="text" 
               name="memo_rule" 
               value="${regra.memo_rule || ''}" 
               onchange="updateRegra(${index}, 'memo_rule', this.value)">
      </td>

      <!-- Ações -->
      <td>
        <button type="button" onclick="removerRule(${index})">🗑️</button>
      </td>
    `;
    corpo.appendChild(linha);
  });
}

/**
 * Remove a regra do array de regras.
 * @param {Array} regras - Array de regras.
 * @param {Number} index - Índice da regra a ser removida.
 * @returns {Array} O array de regras atualizado.
 */
export function removerRegra(regras, index) {
  regras.splice(index, 1);
  return regras;
}

/**
 * Função global para atualizar uma regra (chamada via onchange dos inputs)
 * Atualiza o campo da regra com o novo valor e reaplica as regras nas transações pendentes.
 * Esta função é exposta no objeto global para ser chamada inline no HTML.
 * @param {Number} index - Índice da regra a ser atualizada.
 * @param {String} field - Nome do campo a atualizar.
 * @param {String} value - Novo valor.
 */
window.updateRegra = function(index, field, value) {
  if (!window.regras || !window.regras[index]) return;

  if (field === 'descricao_contain') {
    // Converte a string para array baseada em vírgula
    window.regras[index][field] = value.split(',').map(v => v.trim()).filter(Boolean);
  } else {
    window.regras[index][field] = value.trim();
  }
  
  console.log("Regra " + index + " atualizada:", window.regras[index]);
  
  // Reaplica as regras em todas as transações pendentes
  document.querySelectorAll('#aba-transacoes tbody tr').forEach(row => {
    row.classList.remove('auto-classificado');
    aplicarRegras(row, window.regras);
  });
  
  // Persiste as alterações chamando a função de salvar regras
  window.saveRules();
};

/**
 * Carrega as regras através do endpoint /rules.
 * @param {String} url - O URL do endpoint (padrão: '/rules').
 * @returns {Promise<Array>} - Uma promise que resolve com as regras.
 */
export function carregarRegrasConfig(url = '/rules') {
  return fetch(url)
    .then(response => {
      if (!response.ok) {
        throw new Error(`Erro ao carregar ${url}: ${response.statusText}`);
      }
      return response.json();
    });
}
