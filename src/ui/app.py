import streamlit as st
import sys
import os
import importlib
import base64
import csv
import io

# --- Page Config ---
st.set_page_config(
    page_title="HireSense AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SYSTEM HELPERS ---

def ensure_spacy_model():
    """
    Checks if the spaCy 'en_core_web_sm' model is installed.
    If not, attempts to download it automatically to ensure 'self-healing' deployment.
    """
    try:
        import spacy
        try:
            spacy.load("en_core_web_sm")
        except OSError:
            with st.spinner("Downloading language model for first-time setup..."):
                import subprocess
                subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], capture_output=True)
    except ImportError:
        st.error("Missing dependency: 'spacy'. Please ensure it is in requirements.txt.")

# --- SESSION STATE INITIALIZATION ---
if "shortlist" not in st.session_state:
    st.session_state.shortlist = {}   # { candidate_name: {score, years, skills, verdict} }
if "results_df" not in st.session_state:
    st.session_state.results_df = None
if "blind_mode" not in st.session_state:
    st.session_state.blind_mode = False

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');

    /* Hide default Streamlit overlays but keep Sidebar Toggle visible */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton, [data-testid="stAppDeployButton"] {display: none !important;}
    
    /* Ensure Sidebar Control is always accessible */
    [data-testid="stSidebarCollapseButton"] {
        background-color: #161B22 !important;
        border: 1px solid #30363D !important;
        border-radius: 4px !important;
        color: #C9D1D9 !important;
    }

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'San Francisco', sans-serif !important;
        background-color: #0E1117 !important;
        color: #C9D1D9 !important;
    }

    h1, h2, h3, h4, h5, h6, .candidate-title {
        line-height: 1.6 !important;
        margin-bottom: 8px !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #30363D !important;
        background-color: #161B22 !important;
        border-radius: 8px !important;
        margin-bottom: 12px !important;
    }

    .stTextInput>div>div>input, .stTextArea>div>div>textarea {
        background-color: #0E1117 !important;
        color: #C9D1D9 !important;
        border: 1px solid #30363D !important;
        border-radius: 6px !important;
    }

    .skill-chip {
        display: inline-block;
        background: transparent;
        border: 1px solid #484f58;
        color: #8b949e;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 11px;
        letter-spacing: 0.3px;
        margin: 4px; /* Ensure tags wrap cleanly and have spacing */
        font-weight: 500;
        line-height: 1.4;
    }

    /* Touch target optimizations for interactable elements */
    [data-testid="stExpander"] {
        background-color: #0E1117 !important;
        border: 1px solid #30363D !important;
        border-radius: 6px !important;
        margin-top: 15px !important;
        margin-bottom: 5px !important;
    }
    
    [data-testid="stExpander"] details summary {
        padding: 16px !important; /* Increase click area for expander */
    }

    .stButton > button {
        padding: 12px 24px !important; /* Touch-friendly button padding */
        min-height: 48px !important;
    }

    .candidate-title {
        font-size: 17px;
        font-weight: 600;
        color: #f0f6fc;
        display: flex;
        align-items: center;
        padding-top: 5px;
        flex-wrap: wrap; /* Allows high confidence badge to wrap if necessary */
    }
    .top-match-badge {
        font-size: 10px;
        border: 1px solid #8b949e;
        color: #8b949e;
        padding: 2px 6px;
        border-radius: 3px;
        margin-left: 10px;
        font-weight: 600;
        letter-spacing: 0.5px;
        text-transform: uppercase;
        margin-top: 4px; /* Space when wrapping */
        white-space: nowrap;
    }

    .score-value {
        font-size: 24px;
        font-weight: 300;
        color: #f0f6fc;
        text-align: right;
    }
    .exp-pill {
        font-size: 11px;
        color: #8b949e;
        border: 1px solid #30363d;
        padding: 2px 8px;
        border-radius: 3px;
        font-weight: 500;
        display: inline-block;
        margin-top: 4px;
    }

    .sidebar-brand {
        font-size: 18px;
        font-weight: 600;
        color: #f0f6fc;
        margin-bottom: 2px;
    }
    .sidebar-tagline {
        font-size: 11px;
        color: #484f58;
        margin-bottom: 20px;
    }
    .sidebar-divider {
        height: 1px;
        background-color: #21262d;
        margin: 16px 0;
    }
    
    .mobile-download-link {
        display: none;
        margin-top: 12px;
        color: #58a6ff;
        font-size: 14px;
        text-decoration: none;
        font-weight: 500;
        padding: 10px;
        border: 1px solid #30363d;
        border-radius: 6px;
        text-align: center;
        background-color: #161b22;
    }
    .mobile-download-link:hover {
        background-color: #21262d;
    }

    /* --- MOBILE RESPONSIVE MEDIA QUERY --- */
    @media (max-width: 768px) {
        /* Force Stack for Columns */
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
            margin-bottom: 12px !important;
        }
        
        /* Progress bars spacing when stacked */
        .sub-head {
            margin-top: 16px;
        }

        /* Adjust Brand Size */
        .sidebar-brand {
            font-size: 16px;
        }

        /* Re-align score and badges for mobile */
        .score-value {
            text-align: left;
            font-size: 22px;
            margin-top: 8px;
        }
        .exp-pill {
            text-align: left;
        }

        /* Break candidate title flexbox to wrap properly */
        .candidate-title {
            align-items: flex-start;
            flex-direction: column;
        }
        .top-match-badge {
            margin-left: 0;
            margin-top: 8px;
        }
        
        /* Show download link and limit iframe height */
        .pdf-frame {
            height: 300px !important;
        }
        .mobile-download-link {
            display: block;
        }
    }
</style>
""", unsafe_allow_html=True)

# ─── Module imports ───────────────────────────────────────────────────────────
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

if 'src.nlp.parser' in sys.modules:
    importlib.reload(sys.modules['src.nlp.parser'])
if 'src.nlp.ranker' in sys.modules:
    importlib.reload(sys.modules['src.nlp.ranker'])

with st.spinner("Initializing Models..."):
    ensure_spacy_model()
    try:
        from src.nlp.parser import (
            extract_text, extract_skills,
            extract_structured_entities, calculate_total_experience,
            init_spacy
        )
        from src.nlp.ranker import rank_candidates, init_sentence_transformer
        init_spacy()
        init_sentence_transformer()
    except Exception as e:
        st.error(f"Initialization Error: {str(e)}")
        st.stop()

# ─── Helpers ─────────────────────────────────────────────────────────────────

def render_chips(items: list) -> str:
    """Renders a list of items as monochrome HTML chips."""
    if not items:
        return "<span class='empty-group'>No data detected</span>"
    return "".join([f"<span class='skill-chip'>{i.upper()}</span>" for i in items])

def render_group(label: str, items: list) -> str:
    """Renders a labeled section for grouped data."""
    return f"<div class='group-label'>{label}</div><div style='margin-bottom:4px;'>{render_chips(items)}</div>"

def build_metric(label: str, score: float) -> str:
    """Constructs a custom HTML progress bar for candidate scores."""
    return (
        f"<div style='margin-bottom:8px;'>"
        f"<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;'>"
        f"<span style='font-size:11px;color:#8b949e;font-weight:500;'>{label}</span>"
        f"<span style='font-size:11px;color:#8b949e;'>{score:.1f}%</span>"
        f"</div>"
        f"<div style='background-color:#21262d;height:6px;border-radius:3px;width:100%;overflow:hidden;'>"
        f"<div style='background-color:#8b949e;height:100%;border-radius:3px;width:{score}%;'></div>"
        f"</div></div>"
    )

def render_pdf_preview(file_bytes: bytes, file_name: str):
    """Embeds a base64 encoded PDF viewer inside a Streamlit container."""
    if not file_bytes or not file_name.lower().endswith('.pdf'):
        st.markdown("<div style='color:#484f58;font-size:12px;'>PDF preview only available for .pdf files.</div>", unsafe_allow_html=True)
        return
    b64 = base64.b64encode(file_bytes).decode("utf-8")
    st.markdown(
        f"<iframe class='pdf-frame' src='data:application/pdf;base64,{b64}' width='100%' height='520px' "
        f"style='border:1px solid #30363d;border-radius:6px;background:#0E1117;'></iframe>"
        f"<a href='data:application/pdf;base64,{b64}' download='{file_name}' class='mobile-download-link'>Download Original Document ({file_name})</a>",
        unsafe_allow_html=True
    )

def generate_csv(shortlist: dict, blind_mode: bool) -> bytes:
    """Generates a CSV string from the shortlisted candidates."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Candidate", "Match Score (%)", "Estimated Exp (yrs)", "Key Skills", "Verdict"])
    for i, (name, data) in enumerate(shortlist.items()):
        label = f"Candidate #{i+1}" if blind_mode else name
        writer.writerow([
            label,
            data.get("score", ""),
            data.get("years", ""),
            data.get("skills", ""),
            data.get("verdict", ""),
        ])
    return output.getvalue().encode("utf-8")

def display_name(raw_name: str, idx: int) -> str:
    return f"Candidate #{idx + 1}" if st.session_state.blind_mode else raw_name

# ─── Main App ─────────────────────────────────────────────────────────────────

def main():
    # ══════════════════════════════════════
    # SIDEBAR
    # ══════════════════════════════════════
    with st.sidebar:
        # Brand
        st.markdown("<div class='sidebar-brand'>HireSense AI</div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-tagline'>Intelligent Candidate Screening System</div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)

        # Job Description input
        st.markdown("<div class='sidebar-section-label'>Job Description</div>", unsafe_allow_html=True)
        jd_text = st.text_area("jd_hidden", height=200, placeholder="Paste target description...", label_visibility="collapsed")

        # Settings
        st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-section-label'>Settings</div>", unsafe_allow_html=True)
        st.session_state.blind_mode = st.toggle(
            "Blind Hiring Mode",
            value=st.session_state.blind_mode,
            help="Replaces candidate names with anonymous IDs in results and exports."
        )

        # ── Shortlist Section ──
        st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
        st.markdown("<div class='sidebar-section-label'>Shortlisted Candidates</div>", unsafe_allow_html=True)

        if st.session_state.shortlist:
            for i, (name, data) in enumerate(st.session_state.shortlist.items()):
                label = f"Candidate #{i+1}" if st.session_state.blind_mode else name
                st.markdown(
                    f"<div class='shortlist-item'>"
                    f"<span>{label}</span>"
                    f"<span class='shortlist-score'>{data['score']}%</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)

            # CSV Export
            csv_bytes = generate_csv(st.session_state.shortlist, st.session_state.blind_mode)
            st.download_button(
                label="Download Final Report (.csv)",
                data=csv_bytes,
                file_name="hiresense_shortlist_report.csv",
                mime="text/csv",
                use_container_width=True,
            )
            if st.button("Clear Shortlist", use_container_width=True):
                st.session_state.shortlist = {}
                st.rerun()
        else:
            st.markdown("<div style='color:#484f58;font-size:12px;'>No candidates shortlisted yet.</div>", unsafe_allow_html=True)

        # Footer note
        st.markdown("<div class='sidebar-divider'></div>", unsafe_allow_html=True)
        st.markdown("<div style='color:#484f58;font-size:11px;'>Formula: Semantic 40% + Skills 40% + Experience 20%</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════
    # MAIN AREA
    # ══════════════════════════════════════
    st.title("HireSense AI")
    st.markdown("<p style='color:#8b949e;font-size:14px;margin-bottom:30px;'>Upload candidate dossiers to compute distance vectors against your target parameters.</p>", unsafe_allow_html=True)
    st.markdown("<div style='color:#8b949e;font-size:12px;font-weight:500;margin-bottom:5px;'>UPLOAD FILES (PDF / DOCX)</div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader(
        "doc_hidden", type=["pdf", "docx"],
        accept_multiple_files=True, label_visibility="collapsed"
    )

    if st.button("Process Documents", use_container_width=True):
        if not jd_text.strip():
            st.error("Missing Target Data: Job Description string is empty.")
            st.stop()
        if not uploaded_files:
            st.error("Missing Source Data: No candidate files provided.")
            st.stop()

        with st.spinner("Extracting parameters..."):
            jd_skills = extract_skills(jd_text)

        resumes_data = []
        progress_bar = st.progress(0)

        for i, file in enumerate(uploaded_files):
            progress_bar.progress(i / len(uploaded_files), text=f"Processing: {file.name}")
            file_bytes = file.read()
            res_text = extract_text(file_bytes, file.name)
            resumes_data.append({
                "name": file.name,
                "text": res_text,
                "skills": extract_skills(res_text),
                "entities": extract_structured_entities(res_text),
                "total_years": calculate_total_experience(res_text),
                "file_bytes": file_bytes,
            })

        progress_bar.progress(1.0, text="Computing vectors...")

        with st.spinner("Executing similarity index..."):
            df_ranked = rank_candidates(resumes_data, jd_text, jd_skills)

        # Persist results in session state so they survive reruns triggered by shortlisting
        st.session_state.results_df = df_ranked

    # ── Render Results ──────────────────────────────────────────────────────
    df = st.session_state.results_df
    if df is not None and not df.empty:
        st.markdown("<div style='height:1px;background-color:#30363d;margin:30px 0;'></div>", unsafe_allow_html=True)
        st.markdown("<p style='font-size:16px;font-weight:500;color:#f0f6fc;margin-bottom:20px;'>Computed Results</p>", unsafe_allow_html=True)

        for idx, row in df.iterrows():
            raw_name = row['Candidate File']
            shown_name = display_name(raw_name, idx)
            exp_label = f"{row['Total Years']} yrs" if row['Total Years'] > 0 else "N/A"
            title_badge = "<span class='top-match-badge'>HIGH CONFIDENCE</span>" if idx == 0 else ""
            is_shortlisted = raw_name in st.session_state.shortlist

            with st.container(border=True):

                # Top Row: Name + Score + Shortlist button
                top1, top2, top3 = st.columns([3, 1, 1])
                with top1:
                    st.markdown(
                        f"<div class='candidate-title'>{shown_name} {title_badge}</div>",
                        unsafe_allow_html=True
                    )
                with top2:
                    st.markdown(
                        f"<div class='score-value'>{row['Final Score']:.1f}%</div>"
                        f"<div class='exp-pill'>EXP: {exp_label}</div>",
                        unsafe_allow_html=True
                    )
                with top3:
                    btn_label = "✓ Shortlisted" if is_shortlisted else "+ Shortlist"
                    if st.button(btn_label, key=f"sl_{idx}_{raw_name}", use_container_width=True):
                        if is_shortlisted:
                            del st.session_state.shortlist[raw_name]
                        else:
                            skills_list = row['Technical Skills'] if isinstance(row['Technical Skills'], list) else []
                            st.session_state.shortlist[raw_name] = {
                                "score": row['Final Score'],
                                "years": row['Total Years'],
                                "skills": ", ".join(skills_list[:6]),
                                "verdict": row['Verdict'],
                            }
                        st.rerun()

                # Middle Row: Entities + Metrics
                mid1, mid2 = st.columns([2, 1])
                with mid1:
                    st.markdown(
                        render_group("Skills", row['Technical Skills']) +
                        render_group("Experience", row['Professional Experience']) +
                        render_group("Academic", row['Education']),
                        unsafe_allow_html=True
                    )
                with mid2:
                    st.markdown("<div class='sub-head'>Vector Agreement</div>", unsafe_allow_html=True)
                    st.markdown(build_metric("Semantic Context", row['Semantic Score']), unsafe_allow_html=True)
                    st.markdown(build_metric("Heuristics Index", row['Skill Match']), unsafe_allow_html=True)
                    st.markdown(build_metric("Experience Delta", row['Experience Match']), unsafe_allow_html=True)

                # Expander: Match Insights + PDF Preview
                with st.expander("VIEW MATCH INSIGHTS", expanded=False):
                    st.markdown(
                        f"<div class='verdict-text'>{row['Verdict']}</div>",
                        unsafe_allow_html=True
                    )

                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("<div class='match-title'>Key Matches</div>", unsafe_allow_html=True)
                        if row['Matched Skills']:
                            st.markdown(
                                "".join([f"<div class='match-item'>— {s.upper()}</div>" for s in row['Matched Skills']]),
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown("<div style='color:#8b949e;font-size:12px;'>No explicit intersection identified.</div>", unsafe_allow_html=True)
                    with c2:
                        st.markdown("<div class='gap-title'>Potential Gaps</div>", unsafe_allow_html=True)
                        if row['Gap Skills']:
                            st.markdown(
                                "".join([f"<div class='gap-item'>— {g.upper()}</div>" for g in row['Gap Skills']]),
                                unsafe_allow_html=True
                            )
                        else:
                            st.markdown("<div style='color:#8b949e;font-size:12px;'>No critical parameter gaps identified.</div>", unsafe_allow_html=True)

                    st.markdown("<div class='pdf-section-label'>Original Document Preview</div>", unsafe_allow_html=True)
                    render_pdf_preview(row['File Bytes'], row['File Name'])

if __name__ == "__main__":
    main()
