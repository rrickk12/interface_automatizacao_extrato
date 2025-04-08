// pipeline.js

export function runPipeline() {
  const banco = document.getElementById("banco-select").value;
  const statusDiv = document.getElementById('process-status');
  statusDiv.innerHTML = '⏳ Processando... <span class="spinner"></span>';

  const params = new URLSearchParams();
  params.append("banco", banco);

  fetch('/process', {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: params.toString()
  })
    .then(response => {
      if (!response.ok) throw new Error("Erro ao executar o pipeline.");
      return response.json();
    })
    .then(data => {
      statusDiv.innerHTML = "✅ Pipeline finalizado e relatório atualizado.";
      if (typeof window.updateReport === "function") {
        window.updateReport();
      }
      setTimeout(() => { statusDiv.innerText = ""; }, 3000);
    })
    .catch(error => {
      statusDiv.innerHTML = "❌ Falha: " + error.message;
      console.error("Erro:", error);
    });
}

export function uploadHTML() {
  const input = document.getElementById("html-file-input");
  const banco = document.getElementById("banco-select").value;

  if (!input.files[0]) return;

  const formData = new FormData();
  formData.append("extrato_file", input.files[0]);
  formData.append("banco", banco);

  fetch('/upload_html', {
    method: "POST",
    body: formData
  })
    .then(response => response.json())
    .then(data => {
      console.log("Upload bem-sucedido:", data);
      document.getElementById("process-btn").disabled = false;
    })
    .catch(err => {
      console.error("Erro no upload:", err);
    });
}
