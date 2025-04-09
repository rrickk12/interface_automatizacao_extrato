export function carregarRegras(regras, tableBodySelector) {
  const corpo = document.querySelector(tableBodySelector);
  if (!corpo) return;
  corpo.innerHTML = '';

  regras.forEach((regra, index) => {
    const ruleNumber = index + 1;

    const linha1 = document.createElement('tr');
    linha1.className = 'rule-row rule-row-top';
    linha1.innerHTML = `
      <td colspan="5">
        <div style="margin-bottom: 0.5rem; font-weight: bold; color: #718093;">
          🧠 Regra #${ruleNumber}
        </div>

        <label for="desc-${index}"><strong>Descrição:</strong></label>
        <input id="desc-${index}" type="text" name="descricao_contain"
               value="${(regra.descricao_contain || []).join(', ')}"
               onchange="updateRegra(${index}, 'descricao_contain', this.value)">

        <label for="trans-${index}"><strong>Transação:</strong></label>
        <select id="trans-${index}" name="transaction_type"
                onchange="updateRegra(${index}, 'transaction_type', this.value)">
          <option value="Indefinido" ${regra.transaction_type === 'Indefinido' ? 'selected' : ''}>Indefinido</option>
          <option value="Crédito" ${regra.transaction_type === 'Crédito' ? 'selected' : ''}>Crédito</option>
          <option value="Débito" ${regra.transaction_type === 'Débito' ? 'selected' : ''}>Débito</option>
        </select>

        <label for="contato-${index}"><strong>Contato:</strong></label>
        <input id="contato-${index}" type="text" name="contato_igual"
               value="${regra.contato_igual || ''}"
               onchange="updateRegra(${index}, 'contato_igual', this.value)">
      </td>
    `;

    const linha2 = document.createElement('tr');
    linha2.className = 'rule-row rule-row-bottom';
    linha2.innerHTML = `
      <td colspan="5">

        <label for="tipo-${index}"><strong>Tipo:</strong></label>
        <select id="tipo-${index}" name="tipo" onchange="updateRegra(${index}, 'tipo', this.value)">
          <option value="" ${!regra.tipo ? 'selected' : ''}>Selecione o Tipo</option>
          <option value="Recebimentos" ${regra.tipo === 'Recebimentos' ? 'selected' : ''}>Recebimentos</option>
          <option value="Transferência" ${regra.tipo === 'Transferência' ? 'selected' : ''}>Transferência</option>
        </select>

        <label for="cat-${index}"><strong>Categoria:</strong></label>
        <select id="cat-${index}" name="categoria" onchange="updateRegra(${index}, 'categoria', this.value)">
          <option value="" ${!regra.categoria ? 'selected' : ''}>Selecione a Categoria</option>
          <option value="Locação de equipamentos" ${regra.categoria === 'Locação de equipamentos' ? 'selected' : ''}>Locação de equipamentos</option>
        </select>

        <label for="memo-${index}"><strong>Memo:</strong></label>
        <input id="memo-${index}" type="text" name="memo_rule"
               value="${regra.memo_rule || ''}"
               onchange="updateRegra(${index}, 'memo_rule', this.value)">

        <button type="button" onclick="removerRule(${index})" class="remove-btn">🗑️</button>
      </td>
    `;

    corpo.appendChild(linha1);
    corpo.appendChild(linha2);

    const spacer = document.createElement('tr');
    spacer.className = 'rule-spacer-row';
    spacer.innerHTML = `<td colspan="5"></td>`;
    corpo.appendChild(spacer);
  });
}
