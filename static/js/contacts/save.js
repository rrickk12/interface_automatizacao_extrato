import { jsonToCsv } from './utils.js';

export function saveContacts() {
  const csvData = jsonToCsv(window.contatos);
  fetch('/api/save-contacts', {
    method: 'POST',
    headers: { 'Content-Type': 'text/csv' },
    body: csvData
  })
    .then(res => res.text())
    .then(msg => console.log("Contatos salvos:", msg))
    .catch(err => console.error("Erro ao salvar contatos:", err));
}
