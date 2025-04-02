function updateReport() {
  fetch('/data')
    .then(response => {
      if (!response.ok) throw new Error("Erro ao carregar dados do relatório.");
      return response.json();
    })
    .then(data => {
      const tbody = document.querySelector("#aba-transacoes tbody");
      tbody.innerHTML = ""; // limpa tudo

      data.forEach(item => {
        const tr = document.createElement("tr");
        tr.classList.add("pending");
        tr.setAttribute("data-tipo-transacao", item.transaction_type);

        tr.innerHTML = `
          <td>${item.date || ""}</td>
          <td>${item.description || ""}</td>
          <td>${item.amount || ""}</td>
          <td>${item.transaction_type || ""}</td>
          <td>${item.document || ""}</td>
          <td class="${(!item.contato || !item.contato.cpf_cnpj) ? "contato-alert" : ""}">
            ${item.contato ? item.contato.nome || "-" : "-"}
          </td>
          <td>
            <select name="categoria_tipo" onchange="atualizarCategorias(this)">
              <option value="">Selecione</option>
              ${window.configCategorias && window.configCategorias.tipos_por_transacao 
                ? Object.values(window.configCategorias.tipos_por_transacao)
                    .flat()
                    .map(tipo => `<option value="${tipo}">${tipo}</option>`)
                    .join("")
                : ""
              }
            </select>
          </td>
          <td>
            <select name="categoria_nome">
              <option value="">Selecione</option>
            </select>
          </td>
          <td>
            <button class="status-btn" onclick="setStatus(this, 'validated')">✅</button>
            <button class="status-btn" onclick="setStatus(this, 'canceled')">❌</button>
          </td>
        `;

        // ⬇️ Adiciona ao DOM
        tbody.appendChild(tr);

        // ⬇️ APLICA TUDO DEPOIS DE INSERIR
        if (window.atualizarTipos) window.atualizarTipos(tr);
        if (window.aplicarRegras) window.aplicarRegras(tr);
      });
    })
    .catch(err => console.error(err));
}


// Exemplo de atualização automática após o pipeline:
// static/js/pipeline.js
export function runPipeline() {
  const statusDiv = document.getElementById('process-status');
  statusDiv.innerHTML = '⏳ Processando... <span class="spinner"></span>';

  fetch('/process', { method: 'POST' })
    .then(response => {
      if (!response.ok) throw new Error("Erro ao executar o pipeline.");
      return response.json();
    })
    .then(data => {
      statusDiv.innerHTML = "✅ Pipeline finalizado e relatório atualizado.";
      if (typeof window.updateReport === "function") {
        window.updateReport();
      }
      setTimeout(() => {
        statusDiv.innerText = "";
      }, 3000);
    })
    .catch(error => {
      statusDiv.innerHTML = "❌ Falha: " + error.message;
      console.error("Erro:", error);
    });
}

