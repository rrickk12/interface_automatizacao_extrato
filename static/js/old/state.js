// static/js/state.js

// Captura o estado atual da tabela (seleções de tipos, categorias e status)
export function captureState() {
    let state = [];
    document.querySelectorAll("#aba-transacoes tbody tr").forEach(function(row) {
      let rowState = {
        tipo: row.querySelector('select[name="categoria_tipo"]').value,
        categoria: row.querySelector('select[name="categoria_nome"]').value,
        status: row.className
      };
      state.push(rowState);
    });
    return state;
  }
  
  // Aplica um estado (array de objetos) à tabela
  export function applyState(state) {
    let rows = document.querySelectorAll("#aba-transacoes tbody tr");
    rows.forEach(function(row, index) {
      if (state[index]) {
        row.querySelector('select[name="categoria_tipo"]').value = state[index].tipo;
        if (typeof window.atualizarCategorias === "function") {
          window.atualizarCategorias(row.querySelector('select[name="categoria_tipo"]'));
        }
        row.querySelector('select[name="categoria_nome"]').value = state[index].categoria;
        row.className = state[index].status;
      }
    });
  }
  
  // Funções para salvar, carregar e limpar o estado no servidor
  export function saveStateToServer(state) {
    return fetch('/state/save', {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state)
    }).then(response => response.json());
  }
  
  export function loadStateFromServer() {
    return fetch('/state/load').then(response => {
      if (!response.ok) throw new Error("No state found");
      return response.json();
    });
  }
  
  export function cleanStateOnServer() {
    return fetch('/state/clean', { method: "POST" }).then(response => response.json());
  }
  
  // Pilhas para undo/redo (mantidas no cliente)
  let undoStack = [];
  let redoStack = [];
  
  // Registra o estado atual na pilha de undo
  export function pushStateToUndo() {
    const state = captureState();
    undoStack.push(JSON.stringify(state));
    redoStack = [];
  }
  
  // Desfaz a última ação
  export function undo() {
    if (undoStack.length > 0) {
      redoStack.push(JSON.stringify(captureState()));
      const prevState = JSON.parse(undoStack.pop());
      applyState(prevState);
    } else {
      // alert("No more undo actions available");
    }
  }
  
  // Refaz a última ação desfeita
  export function redo() {
    if (redoStack.length > 0) {
      undoStack.push(JSON.stringify(captureState()));
      const nextState = JSON.parse(redoStack.pop());
      applyState(nextState);
    } else {
      // alert("No more redo actions available");
    }
  }
  
  // Exporta o estado atual para download (arquivo JSON)
  export function exportStateToFile() {
    const state = captureState();
    const blob = new Blob([JSON.stringify(state, null, 2)], {type: "application/json"});
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "state.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
  
  // Importa o estado a partir de um arquivo (arquivo JSON)
  export function importStateFromFile(file) {
    return new Promise((resolve, reject) => {
      if (!file) return reject(new Error("No file provided"));
      const reader = new FileReader();
      reader.onload = function(e) {
        try {
          const state = JSON.parse(e.target.result);
          resolve(state);
        } catch (err) {
          reject(err);
        }
      };
      reader.onerror = () => reject(new Error("Error reading file"));
      reader.readAsText(file);
    });
  }
  