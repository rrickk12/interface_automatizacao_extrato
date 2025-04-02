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
  