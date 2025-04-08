/**
 * Salva o estado das regras no servidor.
 * @param {Array} rules
 * @returns {Promise<object>}
 */
export function saveRulesToServer(rules) {
    return fetch('/rules_state/save', {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(rules)
    }).then(res => res.json());
  }
  
  /**
   * Carrega as regras salvas do servidor.
   * @returns {Promise<Array>}
   */
  export function loadRulesFromServer() {
    return fetch('/rules_state/load')
      .then(res => {
        if (!res.ok) throw new Error("Não há regras salvas no servidor.");
        return res.json();
      });
  }
  
  /**
   * Limpa o estado das regras no servidor.
   * @returns {Promise<object>}
   */
  export function cleanRulesOnServer() {
    return fetch('/rules_state/clean', { method: "POST" })
      .then(res => res.json());
  }
  