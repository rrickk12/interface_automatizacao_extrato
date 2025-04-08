export function applyState(state) {
    const rows = document.querySelectorAll("#aba-transacoes tbody tr");
    rows.forEach((row, index) => {
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
  