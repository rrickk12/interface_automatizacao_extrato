// static/js/rules_state.js

// Funções para salvar, carregar e limpar o estado das regras no servidor
export function saveRulesToServer(rules) {
    return fetch('/rules_state/save', {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(rules)
    }).then(response => response.json());
  }
  
  export function loadRulesFromServer() {
    return fetch('/rules_state/load').then(response => {
      if (!response.ok) throw new Error("No rules state found");
      return response.json();
    });
  }
  
  export function cleanRulesOnServer() {
    return fetch('/rules_state/clean', { method: "POST" }).then(response => response.json());
  }
  

  window.importRules = function(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function(e) {
      try {
        const importedRules = JSON.parse(e.target.result);
        window.regras = importedRules;
        carregarRegras(window.regras, "#tabela-regras tbody");
        alert("Rules imported successfully");
      } catch (err) {
        alert("Failed to import rules: " + err.message);
        console.error(err);
      }
    };
    reader.onerror = () => alert("Error reading file");
    reader.readAsText(file);
  };
  