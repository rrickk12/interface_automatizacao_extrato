// static/js/rules.js

// Atualiza o select de tipos baseado no tipo da transação (caso seja necessário para regras na tabela, se houver)
export function atualizarTipos(row, configCategorias) {
    const tipoTransacao = row.dataset.tipoTransacao;
    const tipoSelect = row.querySelector('select[name="categoria_tipo"]');
    tipoSelect.innerHTML = '<option value="">Selecione</option>';
    if (configCategorias.tipos_por_transacao && configCategorias.tipos_por_transacao[tipoTransacao]) {
      configCategorias.tipos_por_transacao[tipoTransacao].forEach(tipo => {
        tipoSelect.innerHTML += `<option value="${tipo}">${tipo}</option>`;
      });
    }
    const categoriaSelect = row.querySelector('select[name="categoria_nome"]');
    if (categoriaSelect) {
      categoriaSelect.innerHTML = '<option value="">Selecione</option>';
    }
  }
  
  // Atualiza o select de categorias com base no tipo selecionado
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
  
  // Aplica as regras de classificação a uma linha (se necessário em sua interface)
  export function aplicarRegras(row, regras) {
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
      if (regra.contato_igual && contato && !contato.includes(regra.contato_igual)) {
        match = false;
      }
      if (match) {
        const tipoSelect = row.querySelector('select[name="categoria_tipo"]');
        tipoSelect.value = regra.tipo;
        atualizarCategorias(tipoSelect, window.configCategorias);
        const categoriaSelect = row.querySelector('select[name="categoria_nome"]');
        categoriaSelect.value = regra.categoria;
        row.classList.add('auto-classificado');
      }
    });
  }
  
  // Cria uma nova regra a partir dos dados do formulário
  export function criarRegra(form) {
    return {
      descricao_contain: form.descricao_contain.value.split(',').map(v => v.trim()).filter(Boolean),
      descricao_regex: form.descricao_regex.value.trim() || null,
      contato_igual: form.contato_igual.value.trim() || null,
      tipo: form.tipo.value.trim(),
      categoria: form.categoria.value.trim()
    };
  }
  
  // Carrega as regras e exibe na tabela de regras
  export function carregarRegras(regras, tableBodySelector) {
    const corpo = document.querySelector(tableBodySelector);
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
        <td><button onclick="removerRule(${index})">🗑️</button></td>
      `;
      corpo.appendChild(linha);
    });
  }
  
  // Remoção simples de uma regra da lista
  export function removerRegra(regras, index) {
    regras.splice(index, 1);
    return regras;
  }
  