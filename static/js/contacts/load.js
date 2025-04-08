import { limparCsv, csvToJson } from './utils.js';
import { renderContacts } from './render.js';

export function loadContacts() {
  fetch('/entity/contatos_atualizados.csv')
    .then(r => r.text())
    .then(text => {
      const csvLimpo = limparCsv(text);
      window.contatos = csvToJson(csvLimpo);
      renderContacts();
    })
    .catch(err => console.error("Erro ao carregar contatos:", err));
}
