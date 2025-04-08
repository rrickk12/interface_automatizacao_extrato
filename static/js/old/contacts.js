// static/js/contacts.js
function limparCsv(rawText) {
    // Separa as linhas
    const linhas = rawText.split('\n');
  
    // Filtra as linhas removendo aquelas que contêm tokens indesejados
    const linhasLimpas = linhas.filter(linha => {
      // Ignora linhas vazias
      if (!linha.trim()) return false;
      // Ignora linhas que contenham palavras ou caracteres indesejados.
      const tokensInvalidos = ['🗑️ Remover', '{', '}', '[', 'undefined'];
      for (const token of tokensInvalidos) {
        if (linha.includes(token)) {
          return false;
        }
      }
      // Pode ser incluída uma verificação adicional para a existência do delimitador ";"
      if (!linha.includes(';')) return false;
      return true;
    });
    
    return linhasLimpas.join('\n');
  }
  
// Função para converter CSV (com ";" como delimitador) para array de objetos JSON,
// ignorando a coluna "socios" (ela será desconsiderada).
function csvToJson(csvText) {
    // Divide as linhas e remove as vazias
    const lines = csvText.split('\n').filter(line => line.trim() !== '');
    
    // Obtém os cabeçalhos removendo aspas externas
    // Filtra para remover o cabeçalho "socios", se existir
    let headers = lines[0].split(';')
      .map(h => h.trim().replace(/(^"|"$)/g, ''))
      .filter(header => header !== 'socios');
    
    const jsonData = [];
    
    // Para cada linha de dados
    for (let i = 1; i < lines.length; i++) {
      // Separa as colunas; OBS.: Não precisamos fazer tratamento especial para "socios"
      // pois vamos ignorar os dados que estejam nessa coluna.
      const row = lines[i].split(';').map(r => r.trim().replace(/(^"|"$)/g, ''));
      const obj = {};
      // Associa os valores apenas para os índices dos cabeçalhos filtrados.
      // Se o CSV original tiver a coluna "socios", ela será pulada.
      let headerIndex = 0;
      for (let j = 0; j < row.length; j++) {
        // Se o cabeçalho correspondente à posição j for "socios", ignora
        // Aqui, se precisar, pode-se verificar se o header original do CSV (antes de filtrar)
        // era "socios" e pular a posição. Para simplicidade, assumiremos que a
        // coluna "socios" existe apenas no cabeçalho e já foi removida.
        // Assim, usamos somente os valores que correspondem aos cabeçalhos filtrados.
        // Neste exemplo, assumimos que as colunas estão na mesma ordem que o cabeçalho
        // filtrado (ou seja, a coluna "socios" foi removida do CSV fonte também).
        // Se não for o caso, pode-se ajustar o mapeamento manualmente.
        if (headerIndex < headers.length) {
          obj[headers[headerIndex]] = row[j] || '';
          headerIndex++;
        }
      }
      jsonData.push(obj);
    }
    
    return jsonData;
  }
  
  // Função para converter um array de objetos JSON para CSV (usando ";" como delimitador)
  // Aqui, garantimos que a coluna "socios" não seja incluída no CSV exportado.
  function jsonToCsv(jsonArray) {
    if (!jsonArray.length) return "";
    // Usa as chaves do primeiro objeto (que não conterão "socios")
    const headers = Object.keys(jsonArray[0]);
    const lines = [];
    lines.push(headers.join(';'));
    
    jsonArray.forEach(obj => {
      const values = headers.map(header => {
        let val = obj[header] || "";
        // Se o valor contiver ponto e vírgula ou espaços, envolve com aspas
        if (val.includes(';') || val.includes(' ')) {
          val = `"${val}"`;
        }
        return val;
      });
      lines.push(values.join(';'));
    });
    
    return lines.join('\n');
  }
  
  // Inicializa o array global de contatos
  window.contatos = window.contatos || [];
  
  // Função para renderizar a tabela de contatos (sem exibir a coluna "socios")
  export function renderContacts() {
    const tbody = document.querySelector('#tabela-contatos tbody');
    tbody.innerHTML = '';
  
    window.contatos.forEach((contato, index) => {
      const tr = document.createElement('tr');
      // Exibe somente os campos: cpf_cnpj, nome, razao_social e nome_fantasia
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
  
// Exemplo de uso na função loadContacts:
export function loadContacts() {
    fetch('/entity/contatos_atualizados.csv')
      .then(response => {
        if (!response.ok) {
          throw new Error("Erro ao carregar contatos");
        }
        return response.text();
      })
      .then(text => {
        // Aplica o pré-processamento para limpar o texto recebido
        const textoLimpo = limparCsv(text);
        window.contatos = csvToJson(textoLimpo);
        renderContacts();
      })
      .catch(err => console.error("loadContacts:", err));
  }

  // Função para salvar os contatos no CSV do servidor (coluna "socios" não é incluída)
  export function saveContacts() {
    const csvData = jsonToCsv(window.contatos);
    fetch('/api/save-contacts', {
      method: 'POST', // ou PUT, conforme sua implementação
      headers: {
        'Content-Type': 'text/csv'
      },
      body: csvData
    })
    .then(response => {
      if (!response.ok) throw new Error("Erro ao salvar contatos");
      return response.text();
    })
    .then(data => {
      console.log("Contatos salvos com sucesso:", data);
    })
    .catch(err => console.error("saveContacts:", err));
  }
  
  // Função para adicionar um novo contato (não incluindo o campo "socios")
  export function addContact() {
    const novoContato = {
      cpf_cnpj: prompt("Digite o CPF/CNPJ:") || "",
      nome: prompt("Digite o Nome:") || "",
      razao_social: prompt("Digite a Razão Social:") || "",
      nome_fantasia: prompt("Digite o Nome Fantasia:") || "",
      // Como não estamos usando "socios", definimos como vazio
      socios: ""
    };
    window.contatos.push(novoContato);
    renderContacts();
    saveContacts();
  }
  
  // Função para remover um contato
  export function removeContact(index) {
    if (confirm("Remover este contato?")) {
      window.contatos.splice(index, 1);
      renderContacts();
      saveContacts();
    }
  }
  
  // Função para atualizar um campo de contato
  export function updateContact(index, campo, valor) {
    window.contatos[index][campo] = valor;
    console.log(`Contato ${index} atualizado: ${campo} -> ${valor}`);
    saveContacts();
  }
  
  // Função para exportar os contatos para download local
  export function exportContacts() {
    const csvData = jsonToCsv(window.contatos);
    const blob = new Blob([csvData], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "contatos_atualizados.csv";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  
  // Função para importar contatos a partir de um arquivo JSON (mantida se necessário)
  export function importContacts(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(e) {
      try {
        const importedContacts = JSON.parse(e.target.result);
        window.contatos = importedContacts;
        renderContacts();
        saveContacts();
        alert("Contatos importados com sucesso");
      } catch (err) {
        alert("Falha ao importar contatos: " + err.message);
      }
    };
    reader.onerror = () => alert("Erro ao ler o arquivo");
    reader.readAsText(file);
  }
  
  // Registra os Event Listeners após o carregamento do DOM
  document.addEventListener('DOMContentLoaded', () => {
    loadContacts();
  
    const importInput = document.getElementById('import-contacts-input');
    if (importInput) {
      importInput.addEventListener('change', importContacts);
    }
  });
  
  // Função que exibe o formulário de adicionar contato
export function showAddContactForm() {
    document.getElementById('addContactFormContainer').style.display = "block";
  }
  
  // Função que oculta o formulário de adicionar contato
  export function hideAddContactForm() {
    document.getElementById('addContactFormContainer').style.display = "none";
  }
  
  // Processa o envio do formulário, criando um novo contato e salvando-o
  document.getElementById('addContactForm').addEventListener('submit', function(e) {
    e.preventDefault(); // Previne o envio padrão do formulário
  
    // Cria o objeto do novo contato com os valores dos inputs
    const novoContato = {
      cpf_cnpj: document.getElementById('cpf_cnpj').value.trim(),
      nome: document.getElementById('nome').value.trim(),
      razao_social: document.getElementById('razao_social').value.trim(),
      nome_fantasia: document.getElementById('nome_fantasia').value.trim(),
      // Como não estamos usando o campo "socios", podemos definir como vazio
      socios: ""
    };
  
    // Adiciona o novo contato ao array global
    window.contatos.push(novoContato);
    renderContacts();
    saveContacts();
  
    // Limpa os campos do formulário e oculta o container
    this.reset();
    hideAddContactForm();
  });
  // Expor funções para acesso global, se necessário
  window.addContact = addContact;
  window.renderContacts = renderContacts;
  window.removeContact = removeContact;
  window.updateContact = updateContact;
  window.exportContacts = exportContacts;
  window.importContacts = importContacts;
  window.loadContacts = loadContacts;
  window.saveContacts = saveContacts;
  window.showAddContactForm = showAddContactForm;
  window.hideAddContactForm = hideAddContactForm;
  