import os
import json
import re
import time
from pathlib import Path
from uuid import uuid4

from groq import Groq
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from PyPDF2 import PdfReader
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "paper-bold-plus-dev-key")

# ── Folder setup ──────────────────────────────────────────────────────────────
UPLOAD_FOLDER    = Path("uploads")
SUMMARIES_FOLDER = Path("summaries")
UPLOAD_FOLDER.mkdir(exist_ok=True)
SUMMARIES_FOLDER.mkdir(exist_ok=True)

# ── Groq client ───────────────────────────────────────────────────────────────
# Get your FREE API key at: https://console.groq.com
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL  = "llama-3.3-70b-versatile"   # free-tier model

# In-memory paper store:  paper_id -> dict
papers: dict = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_pdf_text(pdf_path: Path) -> str:
    """Extract all text from a PDF using PyPDF2."""
    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            pages.append(t)
    return "\n".join(pages)


def slugify(text: str, max_len: int = 45) -> str:
    """Convert a title string into a safe folder/file name."""
    slug = re.sub(r"[^\w\s-]", "", text).strip().lower()
    slug = re.sub(r"[\s_]+", "_", slug)
    return slug[:max_len].rstrip("_")


def build_markdown(data: dict) -> str:
    """Build a pretty Markdown document from paper data."""
    date_str = time.strftime("%B %d, %Y")
    lines = [
        f"# {data['title']}",
        f"_PaperBold+ · Analyzed on {date_str}_",
        "",
        "---",
        "",
        "## Summary",
        "",
        data["summary"],
        "",
        "## Key Findings",
        "",
    ]
    for f in data["key_findings"]:
        lines.append(f"- {f}")

    lines += ["", "---", "", "## Quiz", ""]
    for i, q in enumerate(data["quiz"]):
        lines.append(f"### Q{i + 1}: {q['question']}")
        lines.append("")
        for j, opt in enumerate(q["options"]):
            marker = "✅ " if j == q["answer"] else "   "
            lines.append(f"- {marker}{chr(65 + j)}) {opt}")
        lines.append("")
        lines.append(f"> 💡 **Explanation:** {q['explanation']}")
        lines.append("")

    return "\n".join(lines)


def save_paper_files(paper_id: str, data: dict) -> tuple[Path, Path]:
    """
    Save summary.md, quiz.json, and full_data.json inside:
        summaries/<slug>_<short_id>/
    Returns (folder_path, summary_md_path).
    """
    slug        = slugify(data["title"])
    folder_name = f"{slug}__{paper_id[:8]}"
    folder      = SUMMARIES_FOLDER / folder_name
    folder.mkdir(parents=True, exist_ok=True)

    md_path = folder / "summary.md"
    md_path.write_text(build_markdown(data), encoding="utf-8")

    quiz_path = folder / "quiz.json"
    quiz_path.write_text(
        json.dumps(data["quiz"], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    full_path = folder / "full_data.json"
    lean = {k: v for k, v in data.items() if k != "text"}
    full_path.write_text(
        json.dumps(lean, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return folder, md_path


def groq_generate(messages: list, max_tokens: int = 1500) -> str:
    """Send messages to Groq and return the text response."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


def analyze_paper(text: str) -> dict:
    """
    Send paper text to Groq and get back structured JSON with
    title, summary, key_findings, and 5-question quiz.
    """
    prompt = f"""Analyze this research paper carefully.
Return ONLY valid JSON — no markdown fences, no extra text, no preamble.

{{
  "title": "full paper title as written in the paper",
  "summary": "3-4 sentence paragraph covering the paper's purpose, methodology, and main contributions",
  "key_findings": ["finding 1", "finding 2", "finding 3", "finding 4"],
  "quiz": [
    {{"question": "question text", "options": ["A text", "B text", "C text", "D text"], "answer": 0, "explanation": "clear explanation of why A is correct"}},
    {{"question": "question text", "options": ["A text", "B text", "C text", "D text"], "answer": 1, "explanation": "clear explanation of why B is correct"}},
    {{"question": "question text", "options": ["A text", "B text", "C text", "D text"], "answer": 2, "explanation": "clear explanation of why C is correct"}},
    {{"question": "question text", "options": ["A text", "B text", "C text", "D text"], "answer": 3, "explanation": "clear explanation of why D is correct"}},
    {{"question": "question text", "options": ["A text", "B text", "C text", "D text"], "answer": 0, "explanation": "clear explanation of why A is correct"}}
  ]
}}

Rules:
- Quiz questions must test real understanding, not trivia.
- Each question should have exactly one clearly correct answer.
- Keep all text concise.

Paper text:
{text[:9000]}
"""

    raw = groq_generate([{"role": "user", "content": prompt}], max_tokens=1500)
    raw = re.sub(r"```json\s*|```\s*", "", raw).strip()
    return json.loads(raw)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "pdf_file" not in request.files:
        return jsonify({"error": "No file selected"}), 400

    file = request.files["pdf_file"]
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400

    paper_id    = str(uuid4())[:12]
    upload_path = UPLOAD_FOLDER / f"{paper_id}.pdf"
    file.save(str(upload_path))

    try:
        # 1. Extract text
        text = extract_pdf_text(upload_path)
        if len(text.strip()) < 200:
            return jsonify({"error": "Could not extract readable text from this PDF. Try a text-based PDF."}), 400

        # 2. Analyze with Groq
        data = analyze_paper(text)
        data["paper_id"] = paper_id
        data["text"]     = text      # kept in memory for chat Q&A

        # 3. Save summary.md + quiz.json to summaries/ folder
        folder, md_path = save_paper_files(paper_id, data)
        data["saved_folder"] = str(folder)
        data["md_path"]      = str(md_path)

        papers[paper_id] = data

        print(f"\n✅ Paper processed: {data['title']}")
        print(f"   Saved to: {folder}/\n")

        return jsonify({"paper_id": paper_id})

    except json.JSONDecodeError as e:
        return jsonify({"error": f"Groq returned invalid JSON. Try again. ({e})"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/viewer/<paper_id>")
def viewer(paper_id):
    if paper_id not in papers:
        return redirect(url_for("index"))
    data = papers[paper_id]
    paper_json = json.dumps({
        k: v for k, v in data.items() if k != "text"
    })
    return render_template("viewer.html", paper=data, paper_json=paper_json)


@app.route("/chat", methods=["POST"])
def chat():
    body     = request.get_json()
    paper_id = body.get("paper_id", "")
    question = body.get("question", "").strip()
    history  = body.get("history", [])   # [{role, content}, ...]

    if paper_id not in papers:
        return jsonify({"error": "Paper session expired. Please re-upload."}), 404
    if not question:
        return jsonify({"error": "Empty question"}), 400

    paper = papers[paper_id]
    text  = paper.get("text", "")[:9000]

    system_prompt = f"""You are an expert research assistant specialising in academic papers.
Answer questions based strictly on the paper below. Be accurate, clear, and concise.
If a question cannot be answered from the paper, say so — do not guess.

Paper title: {paper['title']}

Full paper text:
{text}"""

    # Build messages with history (last 6 turns)
    messages = [{"role": "system", "content": system_prompt}]
    for turn in history[-6:]:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": question})

    answer = groq_generate(messages, max_tokens=800)
    return jsonify({"answer": answer})


@app.route("/download/<paper_id>")
def download(paper_id):
    if paper_id not in papers:
        return "Paper not found", 404
    md_path = Path(papers[paper_id].get("md_path", ""))
    if not md_path.exists():
        return "File not found on disk", 404
    return send_file(str(md_path), as_attachment=True)


if __name__ == "__main__":
    print("─" * 50)
    print("  PaperBold+  →  http://127.0.0.1:5000")
    print("  Summaries saved to: ./summaries/")
    print("  Powered by: Groq (Free Tier)")
    print("─" * 50)
    app.run(debug=True, port=5000)
