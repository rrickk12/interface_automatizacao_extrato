export async function runPipeline() {
  const banco = document.getElementById("banco-select").value;
  const statusDiv = document.getElementById('process-status');
  statusDiv.innerHTML = '⏳ Processando... <span class="spinner"></span>';

  const params = new URLSearchParams();
  params.append("banco", banco);

  try {
    const response = await fetch('/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: params.toString()
    });

    if (!response.ok) throw new Error("Erro ao executar o pipeline.");

    const data = await response.json();
    statusDiv.innerHTML = "✅ Pipeline finalizado e relatório atualizado.";

    if (typeof window.updateReport === "function") {
      window.updateReport();
    }

    setTimeout(() => { statusDiv.innerText = ""; }, 3000);

    return true;
  } catch (error) {
    statusDiv.innerHTML = "❌ Falha: " + error.message;
    console.error("Erro no pipeline:", error);
    return false;
  }
}
