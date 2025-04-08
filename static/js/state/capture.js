export function captureState() {
    const state = [];
    document.querySelectorAll("#aba-transacoes tbody tr").forEach(row => {
      state.push({
        tipo: row.querySelector('select[name="categoria_tipo"]').value,
        categoria: row.querySelector('select[name="categoria_nome"]').value,
        status: row.className
      });
    });
    return state;
  }
  