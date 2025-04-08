export function criarRegra(form) {
    return {
      descricao_contain: form.descricao_contain.value
        .split(',')
        .map(str => str.trim())
        .filter(Boolean),
      transaction_type: form.transaction_type.value.trim() || "Indefinido",
      contato_igual: form.contato_igual.value.trim() || null,
      tipo: form.tipo.value.trim(),
      categoria: form.categoria.value.trim(),
      memo_rule: form.memo_rule.value.trim() || null
    };
  }
  