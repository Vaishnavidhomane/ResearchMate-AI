# ResearchMate-AI
Upload any research paper PDF and get an AI-powered summary, key findings, quiz, and chat assistant — free
<div align="center">

# 📄 ResearchMate AI

### Upload any research paper PDF and instantly get AI-powered summaries, key findings, quizzes, and a chat assistant — completely free.


</div>

---

## 🌟 What is ResearchMate AI?

ResearchMate AI is a web app that helps students and researchers **understand research papers faster**. Just upload a PDF and within seconds you get:

- A clean summary
- Key findings pulled from the paper
- A 5-question quiz to test your understanding
- A chat assistant to ask anything about the paper

No subscriptions. No credit card. 100% free.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 📤 **PDF Upload** | Upload any research paper in PDF format |
| 🧠 **AI Summary** | Clean 3-4 sentence summary of the paper |
| 🔍 **Key Findings** | Most important points extracted automatically |
| 📝 **Auto Quiz** | 5 multiple choice questions with explanations |
| 💬 **Chat Assistant** | Ask anything about the paper and get accurate answers |
| 💾 **Download Summary** | Export full summary + quiz as a Markdown file |

---

## 🚀 Live Demo

👉 **[researchmate-ai-4sdf.onrender.com](https://researchmate-ai-4sdf.onrender.com)**

> ⚠️ Hosted on Render free tier — first load may take 30 seconds to wake up.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, Flask |
| AI Model | Google Gemini 1.5 Flash |
| PDF Parsing | PyPDF2 |
| Frontend | HTML, CSS, JavaScript |
| Hosting | Render |

---

## ⚙️ Run Locally

### 1. Clone the repo

```bash
git clone https://github.com/Vaishnavidhomane/ResearchMate-AI.git
cd ResearchMate-AI
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in:

```
GROQ_API_KEY=your_groq_api_key_here
SECRET_KEY=any_random_string
```

Get your **free** Groq API key at 👉 [console.groq.com](https://console.groq.com)

### 4. Run the app

```bash
python app.py
```

Open your browser at `http://127.0.0.1:5000` 🎉

---

## 📁 Project Structure

```
ResearchMate-AI/
├── app.py               # Main Flask application
├── templates/
│   ├── index.html       # Upload page
│   └── viewer.html      # Summary + quiz + chat page
├── uploads/             # Temporary uploaded PDFs
├── summaries/           # Auto-saved summaries (markdown + json)
├── Dockerfile           # For container deployment
├── .env.example         # Environment variables template
├── requirements.txt     # Python dependencies
└── README.md
```

---

## 🔑 Environment Variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Your Groq API key — free at [console.groq.com](https://console.groq.com) |
| `SECRET_KEY` | Any random string for Flask sessions |

---

## 📦 Requirements

```
flask>=3.0.0
groq
PyPDF2>=3.0.0
python-dotenv>=1.0.0
gunicorn
```

---

## ⚠️ Notes

- Only **text-based PDFs** are supported (not scanned images)
- Make sure `.env` is in your `.gitignore` — never commit your API keys!
- Uploaded PDFs are stored temporarily in the `uploads/` folder

---

## 🙌 Made by

**Vaishnavi Dhomane** — [github.com/Vaishnavidhomane](https://github.com/Vaishnavidhomane)

---

## 📄 License

MIT License — free to use and modify.
