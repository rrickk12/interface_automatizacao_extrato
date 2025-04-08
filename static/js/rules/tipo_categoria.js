export function atualizarTipos(row, configCategorias) {
    const tipoTransacao = row.dataset.tipoTransacao || "Indefinido";
    const tipoSelect = row.querySelector('select[name="categoria_tipo"]');
    const categoriaSelect = row.querySelector('select[name="categoria_nome"]');
  
    if (tipoSelect) {
      tipoSelect.innerHTML = '<option value="">Selecione</option>';
      if (configCategorias?.tipos_por_transacao?.[tipoTransacao]) {
        configCategorias.tipos_por_transacao[tipoTransacao].forEach(tipo => {
          tipoSelect.innerHTML += `<option value="${tipo}">${tipo}</option>`;
        });
      }
    }
  
    if (categoriaSelect) categoriaSelect.innerHTML = '<option value="">Selecione</option>';
  }
  
  export function atualizarCategorias(selectElem, configCategorias) {
    const row = selectElem.closest('tr');
    const categoriaSelect = row.querySelector('select[name="categoria_nome"]');
    const tipoSelecionado = selectElem.value;
  
    categoriaSelect.innerHTML = '<option value="">Selecione</option>';
  
    const sugeridas = [];
    const outras = [];
  
    if (configCategorias?.categorias_por_tipo) {
      for (const [categoria, tipos] of Object.entries(configCategorias.categorias_por_tipo)) {
        if (tipos.includes(tipoSelecionado)) {
          sugeridas.push(categoria);
        } else {
          outras.push(categoria);
        }
      }
    }
  
    sugeridas.forEach(cat => {
      categoriaSelect.innerHTML += `<option value="${cat}">${cat}</option>`;
    });
  
    if (outras.length > 0) categoriaSelect.innerHTML += '<option disabled>──────────────</option>';
  
    outras.forEach(cat => {
      categoriaSelect.innerHTML += `<option value="${cat}">${cat}</option>`;
    });
  }
  