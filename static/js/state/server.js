export function saveStateToServer(state) {
    return fetch('/state/save', {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state)
    }).then(r => r.json());
  }
  
  export function loadStateFromServer() {
    return fetch('/state/load')
      .then(r => {
        if (!r.ok) throw new Error("Nenhum estado encontrado");
        return r.json();
      });
  }
  
  export function cleanStateOnServer() {
    return fetch('/state/clean', { method: "POST" }).then(r => r.json());
  }
      