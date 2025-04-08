import { jsonToCsv, csvToJson, limparCsv } from './utils.js';


export function exportContacts() {
    const csv = jsonToCsv(window.contatos);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "contatos_atualizados.csv";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }
  
  export function importContacts(event) {
    const file = event.target.files[0];
    if (!file) return;
  
    const reader = new FileReader();
    reader.onload = e => {
      try {
        window.contatos = JSON.parse(e.target.result);
        renderContacts();
        saveContacts();
        alert("Contatos importados com sucesso.");
      } catch (err) {
        alert("Erro ao importar: " + err.message);
      }
    };
    reader.readAsText(file);
  }
  