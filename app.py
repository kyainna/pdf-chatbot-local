from flask import Flask, render_template, request, jsonify, send_from_directory
import pdfplumber
import os
import threading
import time
from dotenv import load_dotenv       # ✅ NEW
from openai import OpenAI

load_dotenv()                        # ✅ NEW: load .env file

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# ✅ SECURE: Use key from environment variable
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# Ensure upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# -------------------------------
# Auto-delete helper
# -------------------------------
def schedule_file_delete(filepath, delay=1800):  # 1800 sec = 30 minutes
    def delete_file():
        time.sleep(delay)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"🗑️ Auto-deleted: {filepath}")
            except Exception as e:
                print(f"⚠️ Failed to delete {filepath}: {e}")
    threading.Thread(target=delete_file, daemon=True).start()

# -------------------------------
# Routes
# -------------------------------
@app.route('/')
def index():
    return render_template('index.html')

# Serve uploaded files for pdf.js
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# Upload PDF
@app.route('/upload', methods=['POST'])
def upload_pdf():
    if 'pdf' not in request.files:
        return "No file part", 400
    file = request.files['pdf']
    if file.filename == '':
        return "No selected file", 400
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(filepath)

    # Schedule auto-delete in 30 minutes
    schedule_file_delete(filepath, delay=1800)

    # Extract text
    text = ""
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    return jsonify({"text": text, "filename": file.filename})

# Chat with AI
@app.route('/ask', methods=['POST'])
def ask():
    data = request.get_json()
    user_question = data.get('question', '')
    pdf_text = data.get('pdf_text', '')

    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",  # use 4o-mini if you prefer
            messages=[
                {"role": "system", "content": "You are an assistant that answers questions based on a PDF."},
                {"role": "user", "content": f"PDF:\n{pdf_text}\n\nQuestion: {user_question}"}
            ]
        )
        answer = response.choices[0].message.content
    except Exception as e:
        answer = f"⚠️ Error: {str(e)}"

    return jsonify({"answer": answer})

if __name__ == '__main__':
    app.run(debug=True)
