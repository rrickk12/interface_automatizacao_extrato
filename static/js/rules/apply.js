export function aplicarRegras(row, regras) {
    const desc = row.cells[1] ? row.cells[1].innerText : "";
    const contatoElem = row.querySelector('input[name="contato_parcial"]');
    const contato = contatoElem ? contatoElem.value : (row.cells[5]?.innerText || "");
    const transacaoTipo = row.dataset.tipoTransacao || "Indefinido";
  
    regras.forEach(regra => {
      let match = true;
  
      if (regra.descricao_contain?.length) {
        match = regra.descricao_contain.every(palavra => desc.includes(palavra));
      }
  
      if (match && regra.contato_igual) {
        if (!contato || !contato.includes(regra.contato_igual)) match = false;
      }
  
      if (match && regra.transaction_type && regra.transaction_type !== "Indefinido") {
        if (regra.transaction_type.toLowerCase() !== transacaoTipo.toLowerCase()) match = false;
      }
  
      if (match) {
        const tipoSelect = row.querySelector('select[name="categoria_tipo"]');
        if (tipoSelect) {
          tipoSelect.value = regra.tipo;
          window.atualizarCategorias(tipoSelect, window.configCategorias);
        }
  
        const categoriaSelect = row.querySelector('select[name="categoria_nome"]');
        if (categoriaSelect) categoriaSelect.value = regra.categoria;
  
        const memoInput = row.querySelector('input[name="memo"]');
        if (memoInput) memoInput.value = regra.memo_rule || "";
  
        if (contatoElem && regra.contato_igual) {
          contatoElem.value = regra.contato_igual;
        }
  
        row.classList.add('auto-classificado');
      }
    });
  }
  