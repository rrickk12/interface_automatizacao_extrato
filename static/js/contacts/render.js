export function renderContacts() {
    const tbody = document.querySelector('#tabela-contatos tbody');
    if (!tbody) return;
    tbody.innerHTML = '';
  
    window.contatos.forEach((contato, index) => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><input type="text" value="${contato.cpf_cnpj}" onchange="updateContact(${index}, 'cpf_cnpj', this.value)" /></td>
        <td><input type="text" value="${contato.nome}" onchange="updateContact(${index}, 'nome', this.value)" /></td>
        <td><input type="text" value="${contato.razao_social}" onchange="updateContact(${index}, 'razao_social', this.value)" /></td>
        <td><input type="text" value="${contato.nome_fantasia}" onchange="updateContact(${index}, 'nome_fantasia', this.value)" /></td>
        <td><button onclick="removeContact(${index})">🗑️ Remover</button></td>
      `;
      tbody.appendChild(tr);
    });
  }
  