export function showAddContactForm() {
    document.getElementById('addContactFormContainer').style.display = "block";
  }
  
  export function hideAddContactForm() {
    document.getElementById('addContactFormContainer').style.display = "none";
  }
  
  export function setupFormListener() {
    document.getElementById('addContactForm').addEventListener('submit', function(e) {
      e.preventDefault();
      const novoContato = {
        cpf_cnpj: document.getElementById('cpf_cnpj').value.trim(),
        nome: document.getElementById('nome').value.trim(),
        razao_social: document.getElementById('razao_social').value.trim(),
        nome_fantasia: document.getElementById('nome_fantasia').value.trim(),
        socios: ""
      };
      window.contatos.push(novoContato);
      renderContacts();
      saveContacts();
      this.reset();
      hideAddContactForm();
    });
  }
  