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
        console.error("Erro no pipeline:", error);
      });
  }
  