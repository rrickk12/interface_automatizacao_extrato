export function renderContacts() {
  const tbody = document.querySelector('#tabela-contatos tbody');
  if (!tbody) return;

  tbody.innerHTML = '';

  (window.contatos || []).forEach((contato, index) => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td><input type="text" value="${contato.cpf_cnpj || ''}" data-field="cpf_cnpj" data-index="${index}"></td>
      <td><input type="text" value="${contato.nome || ''}" data-field="nome" data-index="${index}"></td>
      <td><input type="text" value="${contato.razao_social || ''}" data-field="razao_social" data-index="${index}"></td>
      <td><input type="text" value="${contato.nome_fantasia || ''}" data-field="nome_fantasia" data-index="${index}"></td>
      <td>
        <button class="btn-remover" data-index="${index}" title="Remover contato">🗑️ Remover</button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  // Eventos de edição
  tbody.querySelectorAll('input').forEach(input => {
    input.addEventListener('input', () => {
      const index = parseInt(input.dataset.index);
      const field = input.dataset.field;
      window.contatos[index][field] = input.value;
      window.saveContacts(); // Atualiza o estado a cada edição
    });
  });

  // Evento de remover
  tbody.querySelectorAll('.btn-remover').forEach(btn => {
    btn.addEventListener('click', () => {
      const index = parseInt(btn.dataset.index);
      window.contatos.splice(index, 1);
      renderContacts();  // Re-renderizar após remoção
      window.saveContacts();  // Salvar estado
    });
  });
}
