import streamlit as st
import fitz  # PyMuPDF
import docx
import io
import re
from datetime import datetime

@st.cache_resource
def init_spacy():
    """
    Loads and caches the spaCy English language model.
    
    Returns:
        spacy.Language: The loaded 'en_core_web_sm' model, or None if unavailable.
    """
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except ImportError:
        return None
    except OSError:
        st.error("SpaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
        return None

# ─────────────────────────────────────────────
# CATEGORY 1: Technical Skills
# ─────────────────────────────────────────────
TECHNICAL_SKILLS = {
    "python", "java", "c++", "c#", "golang", "rust", "javascript", "typescript",
    "react", "angular", "vue", "node.js", "django", "flask", "fastapi", "spring",
    "docker", "kubernetes", "terraform", "ci/cd", "git", "linux", "bash",
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch",
    "aws", "gcp", "azure", "cloud", "devops", "microservices", "rest api",
    "machine learning", "deep learning", "nlp", "pytorch", "tensorflow",
    "scikit-learn", "pandas", "numpy", "data analysis", "data science",
    "spacy", "streamlit", "spark", "hadoop",
    "photoshop", "illustrator", "figma", "sketch", "indesign", "after effects",
    "premiere", "canva", "adobe xd", "adobe cc",
    "wordpress", "hubspot", "mailchimp", "google analytics", "google ads",
    "facebook ads", "semrush", "ahrefs", "hootsuite",
    "seo", "sem", "ppc", "crm", "erp", "salesforce",
    "excel", "powerpoint", "ms word", "microsoft office", "google workspace",
    "jira", "confluence", "notion", "slack", "trello",
    "autocad", "solidworks", "matlab",
}

# ─────────────────────────────────────────────
# CATEGORY 2: Professional Experience (job titles)
# ─────────────────────────────────────────────
EXPERIENCE_KEYWORDS = {
    "graphic designer", "senior graphic designer", "junior graphic designer",
    "content writer", "senior content writer", "copywriter", "technical writer",
    "content strategist", "content manager", "content creator",
    "digital marketer", "marketing manager", "brand manager", "social media manager",
    "seo specialist", "seo analyst", "marketing analyst",
    "software engineer", "software developer", "backend developer", "frontend developer",
    "full stack developer", "full-stack developer", "data scientist", "data analyst",
    "machine learning engineer", "ai engineer", "nlp engineer",
    "product manager", "product designer", "ux designer", "ui designer",
    "ui/ux designer", "web designer", "creative director", "art director",
    "motion designer", "video editor", "photographer",
    "project manager", "business analyst", "hr manager", "recruiter",
    "talent acquisition", "operations manager", "team lead", "tech lead",
    "consultant", "intern", "associate", "manager", "director", "vp", "cto", "ceo",
}

# ─────────────────────────────────────────────
# CATEGORY 3: Education & Certifications
# ─────────────────────────────────────────────
DEGREE_KEYWORDS = {
    "phd", "ph.d", "doctorate",
    "master", "masters", "m.s", "m.sc", "mba", "m.tech", "m.e",
    "bachelor", "bachelors", "b.s", "b.sc", "b.a", "b.tech", "b.e", "bca", "bba", "b.com",
    "diploma", "associate degree", "high school",
    "certified", "certification", "certificate",
    "aws certified", "google certified", "microsoft certified",
    "pmp", "ccna", "cpa", "cfa",
}

# ─────────────────────────────────────────────
# Month name → integer mapping
# ─────────────────────────────────────────────
MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    "january": 1, "february": 2, "march": 3, "april": 4, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

# ─────────────────────────────────────────────
# Text Extraction
# ─────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts raw text from a PDF file using PyMuPDF.

    Args:
        file_bytes (bytes): The binary content of the PDF file.

    Returns:
        str: The extracted text content.
    """
    text = ""
    try:
        pdf_document = fitz.open(stream=file_bytes, filetype="pdf")
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)
            text += page.get_text()
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text.strip()

def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Extracts raw text from a DOCX file using python-docx.

    Args:
        file_bytes (bytes): The binary content of the DOCX file.

    Returns:
        str: The extracted text content.
    """
    text = ""
    try:
        doc = docx.Document(io.BytesIO(file_bytes))
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX: {e}")
    return text.strip()

def extract_text(file_bytes: bytes, file_name: str) -> str:
    """
    General purpose text extraction helper that handles PDF, DOCX, or UTF-8 text.

    Args:
        file_bytes (bytes): The binary content of the file.
        file_name (str): The name of the file to determine its type.

    Returns:
        str: The extracted text content.
    """
    if file_name.lower().endswith('.pdf'):
        return extract_text_from_pdf(file_bytes)
    elif file_name.lower().endswith('.docx'):
        return extract_text_from_docx(file_bytes)
    else:
        try:
            return file_bytes.decode('utf-8')
        except UnicodeDecodeError:
            return ""

# ─────────────────────────────────────────────
# Phrase Matching Core
# ─────────────────────────────────────────────

def _find_phrases(text_lower: str, phrase_set: set) -> list:
    """
    Internal helper to match multi-word phrases longest-first from a set.

    Args:
        text_lower (str): The lowercased text to search through.
        phrase_set (set): A set of predefined keywords or phrases.

    Returns:
        list: A sorted list of matched phrases.
    """
    found = set()
    sorted_phrases = sorted(phrase_set, key=len, reverse=True)
    for phrase in sorted_phrases:
        pattern = r'\b' + re.escape(phrase) + r'\b'
        if re.search(pattern, text_lower):
            found.add(phrase)
    return sorted(list(found))

# ─────────────────────────────────────────────
# Experience Duration Calculator
# ─────────────────────────────────────────────

def _parse_date_token(token: str) -> datetime | None:
    """
    Converts various date format tokens into a python datetime object.

    Handles 'Present', 'Current', 'YYYY', 'Mon YYYY', 'MM/YYYY'.

    Args:
        token (str): The date string to parse.

    Returns:
        datetime: The parsed date, or None if invalid.
    """
    token = token.strip().lower()

    # Present / current / now → today
    if token in ("present", "current", "now", "till date", "to date"):
        return datetime.today()

    # Plain year: e.g. "2019"
    if re.fullmatch(r'\d{4}', token):
        return datetime(int(token), 1, 1)

    # Month abbreviation + year: "jan 2020", "march 2019"
    m = re.match(r'^([a-z]+)\s+(\d{4})$', token)
    if m:
        month_str, year_str = m.group(1), m.group(2)
        month = MONTH_MAP.get(month_str[:3])
        if month:
            return datetime(int(year_str), month, 1)

    # MM/YYYY or MM-YYYY
    m = re.match(r'^(\d{1,2})[/\-](\d{4})$', token)
    if m:
        return datetime(int(m.group(2)), int(m.group(1)), 1)

    return None

def calculate_total_experience(text: str) -> float:
    """
    Detects all date ranges in the candidate text and sums their durations.

    Uses complex regex to catch 'Jan 2020 - Present', '2015 to 2019', etc.

    Args:
        text (str): The candidate's resume/CV text.

    Returns:
        float: Total estimated professional experience in years, rounded to 1 decimal.
    """
    if not text:
        return 0.0

    text_lower = text.lower()

    # Separator alternatives: –, -, to, till, until
    SEP = r'\s*(?:–|—|-|to|till|until)\s*'

    # Month+Year token pattern
    MON_YR = r'(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{4}'
    # MM/YYYY token pattern
    MMYYYY = r'\d{1,2}[/\-]\d{4}'
    # Plain year
    YYYY = r'\d{4}'
    # Terminal tokens
    PRESENT = r'(?:present|current|now|till\s+date|to\s+date)'

    # Flexible date token = any of the above
    DATE_TOKEN = f'(?:{MON_YR}|{MMYYYY}|{YYYY}|{PRESENT})'

    pattern = re.compile(
        DATE_TOKEN + SEP + DATE_TOKEN,
        re.IGNORECASE
    )

    total_months = 0.0
    for match in pattern.finditer(text_lower):
        full = match.group(0)
        # Split on separator
        parts = re.split(r'\s*(?:–|—|-|to|till|until)\s*', full, maxsplit=1, flags=re.IGNORECASE)
        if len(parts) != 2:
            continue
        start_dt = _parse_date_token(parts[0].strip())
        end_dt = _parse_date_token(parts[1].strip())
        if start_dt and end_dt and end_dt >= start_dt:
            delta_months = (end_dt.year - start_dt.year) * 12 + (end_dt.month - start_dt.month)
            total_months += delta_months

    return round(total_months / 12.0, 1)

# ─────────────────────────────────────────────
# Structured Entity Extraction
# ─────────────────────────────────────────────

def extract_structured_entities(text: str) -> dict:
    """
    Parses candidate text into structured categories for UI rendering.

    Utilizes predefined phrase sets and spaCy NER for institutional detection.

    Args:
        text (str): The raw text of the resume.

    Returns:
        dict: A dictionary containing lists for 'technical_skills', 
              'professional_experience', and 'education'.
    """
    if not text:
        return {"technical_skills": [], "professional_experience": [], "education": []}

    text_lower = text.lower()

    technical = _find_phrases(text_lower, TECHNICAL_SKILLS)
    experience = _find_phrases(text_lower, EXPERIENCE_KEYWORDS)
    education = _find_phrases(text_lower, DEGREE_KEYWORDS)

    # spaCy NER for university/institution names
    nlp = init_spacy()
    if nlp is not None:
        doc = nlp(text)
        for ent in doc.ents:
            if ent.label_ in ["ORG", "GPE"]:
                clean = ent.text.strip()
                clean_lower = clean.lower()
                if any(kw in clean_lower for kw in ["university", "college", "school", "institute", "academy"]):
                    if clean_lower not in [e.lower() for e in education] and len(clean) > 3:
                        education.append(clean)

    return {
        "technical_skills": technical,
        "professional_experience": experience,
        "education": education,
    }

def extract_skills(text: str) -> list:
    """
    Extracts a flat list of technical skills for use in similarity scoring.

    Args:
        text (str): The raw text of the resume/CV.

    Returns:
        list: A list of matched technical keywords.
    """
    if not text:
        return []
    return _find_phrases(text.lower(), TECHNICAL_SKILLS)
