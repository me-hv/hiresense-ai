# HireSense AI

> **Intelligent Resume Screening & Candidate Ranking System**

HireSense AI automates the recruitment pipeline by parsing resumes, extracting structured candidate data, and ranking applicants against a job description using semantic similarity, skill intersection, and temporal experience analysis — delivering explainable, bias-aware results in a professional dashboard.

---

## Overview

Traditional keyword-based resume screening misses context, rewards keyword stuffing, and introduces unconscious bias. HireSense AI solves this with a multi-layer NLP engine:

- **Semantic Match** — Sentence Transformers (`all-MiniLM-L6-v2`) encode the JD and resume into vector space; cosine similarity measures true contextual alignment, not just keyword overlap.
- **Skill Intersection** — A domain-aware keyword dictionary (100+ terms across Engineering, Design, Marketing, and more) identifies exact and partial skill matches against the JD.
- **Experience Analysis** — Regex-based date range parsing sums all employment periods to produce a verified `total_years` value, scored against the JD's stated requirement with a graduated penalty tier.
- **Blind Hiring Mode** — One-click anonymization of candidate names across the dashboard and exported reports to reduce unconscious bias.
- **Match Insights** — Every candidate receives a data-driven "System Verdict" with a list of confirmed Key Matches and specific Potential Gaps.

---

## Key Features

| Feature | Description |
|---|---|
| **Contextual Ranking** | Transformers-based semantic matching for high-precision alignment. |
| **Structured Parsing** | Skills, Experience, and Education categorized into separate high-readability groups. |
| **Experience Engine** | Intelligent date-range detection tracks career duration (e.g., `Jan 2020 – Present`). |
| **Explainable AI** | Plain-language match verdicts with color-coded matches and gaps. |
| **Blind Hiring** | Toggleable anonymization (e.g., `Candidate #1`) to ensure merit-based screening. |
| **Shortlist & Export** | Persistent session-state shortlisting with one-click `.csv` reporting. |
| **Inline PDF Preview** | Direct base64-encoded PDF rendering inside candidate insight panels. |
| **Self-Healing Design** | Automated spaCy model installation on first-time deployment. |

---

## Scoring Formula

```
Final Score = (Semantic Match × 0.40) + (Skill Match × 0.40) + (Experience Match × 0.20)
```

The system uses a pessimistic scoring model: empty fields or missing requirements default to low scores (`0% - 5%`) rather than "hallucinated" matches.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Interface** | Streamlit (Custom Monochrome CSS) |
| **Semantic AI** | `sentence-transformers` (`all-MiniLM-L6-v2`), `scikit-learn` |
| **Entity Extraction** | `spaCy` (`en_core_web_sm`) |
| **File Parsing** | `PyMuPDF` (PDFs), `python-docx` (Word Docs) |
| **Data Engine** | `pandas`, `re`, `datetime` |
| **Runtime** | Python 3.10+ |

---

## Project Structure

```
HireSense AI/
├── src/
│   ├── nlp/
│   │   ├── parser.py          # Data extraction and experience calculation
│   │   └── ranker.py          # Scoring engine and verdict generation
│   └── ui/
│       └── app.py             # SaaS-style monochrome dashboard
├── requirements.txt           # Python dependencies
├── packages.txt               # System dependencies (for Linux/Streamlit Cloud)
├── start.bat                  # Windows quick-launch script
└── README.md
```

---

## How to Run

### 1. Clone & Setup

```bash
git clone https://github.com/me-hv/hiresense-ai.git
cd hiresense-ai
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# Activate (macOS/Linux)
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Launch

```bash
streamlit run src/ui/app.py
```

> **Note:** On the first run, the app will automatically download the required spaCy language model.

---

## Usage Workflow

1. **Set Target:** Paste the target Job Description in the sidebar.
2. **Upload Docs:** Drop multiple resumes (PDF/DOCX) into the uploader.
3. **Analyze:** Click **Process Documents** to generate vector agreements.
4. **Evaluate:** Use **VIEW MATCH INSIGHTS** to see the AI's reasoning.
5. **Shortlist:** Mark top candidates and download the **Final Report**.

---

## Privacy & Security

- **Local Processing:** Resumes are processed in-memory; no files are saved to disk.
- **Anonymization:** Blind hiring mode protects candidate identity throughout the workflow.
- **No Cloud APIs:** All NLP inference runs locally on your machine.

---

## License

MIT License. See `LICENSE` for details.
