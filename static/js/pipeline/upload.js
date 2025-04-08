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
  