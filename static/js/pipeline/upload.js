export function uploadHTML(event) {
  event.preventDefault();

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
    .then(async data => {
      console.log("✅ Upload bem-sucedido:", data);

      // Corrigido o ID aqui:
      const btnPipeline = document.getElementById("btn-run-pipeline");
      if (btnPipeline) btnPipeline.disabled = false;

      const success = await window.runPipeline();
      if (success) {
        location.reload();
      }
    })
    .catch(err => {
      console.error("❌ Erro no upload:", err);
    });
}
