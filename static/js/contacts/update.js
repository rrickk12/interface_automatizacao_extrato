export function updateContact(index, campo, valor) {
    window.contatos[index][campo] = valor;
    console.log(`Contato ${index} atualizado: ${campo} → ${valor}`);
    saveContacts();
  }
  
  export function removeContact(index) {
    if (confirm("Remover este contato?")) {
      window.contatos.splice(index, 1);
      renderContacts();
      saveContacts();
    }
  }
  