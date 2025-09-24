let pdfText = "";
let pdfFileName = "";

// Setup PDF.js worker
pdfjsLib.GlobalWorkerOptions.workerSrc =
  "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js";

// Upload handler
function handleUpload(e) {
  let file = e.target.files[0];
  let formData = new FormData();
  formData.append("pdf", file);

  fetch("/upload", { method: "POST", body: formData })
    .then((res) => res.json())
    .then((data) => {
      pdfText = data.text;
      pdfFileName = data.filename;
      renderPDF(pdfFileName);
    })
    .catch((err) => console.error("Upload error:", err));
}
document.getElementById("pdf-upload").addEventListener("change", handleUpload);

// Render PDF pages
function renderPDF(fileName) {
  const url = `/uploads/${fileName}`;
  const container = document.getElementById("pdf-container");
  container.innerHTML = "";

  pdfjsLib.getDocument(url).promise.then((pdf) => {
    for (let i = 1; i <= pdf.numPages; i++) {
      pdf.getPage(i).then((page) => {
        const viewport = page.getViewport({ scale: 1.2 });
        const canvas = document.createElement("canvas");
        const context = canvas.getContext("2d");
        canvas.height = viewport.height;
        canvas.width = viewport.width;
        container.appendChild(canvas);
        page.render({ canvasContext: context, viewport: viewport });
      });
    }
  });
}

// Chat handler
document.getElementById("ask-btn").addEventListener("click", function () {
  const question = document.getElementById("question").value;
  if (!question) return;

  const chatBox = document.getElementById("chat-box");
  chatBox.innerHTML += `<div class="user-msg">You: ${question}</div>`;
  chatBox.innerHTML += `<div id="typing-indicator" class="ai-msg"><i>AI is typing...</i></div>`;
  chatBox.scrollTop = chatBox.scrollHeight;

  fetch("/ask", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question: question, pdf_text: pdfText }),
  })
    .then((res) => res.json())
    .then((data) => {
      document.getElementById("typing-indicator").remove();
      chatBox.innerHTML += `<div class="ai-msg">AI: ${data.answer}</div>`;
      chatBox.scrollTop = chatBox.scrollHeight;
    })
    .catch((err) => {
      document.getElementById("typing-indicator").remove();
      chatBox.innerHTML += `<div class="ai-msg">⚠️ Error: ${err}</div>`;
    });

  document.getElementById("question").value = "";
});
