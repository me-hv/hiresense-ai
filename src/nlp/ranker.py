"""
HIRESENSE AI - RANKING ENGINE
------------------------------
Scoring Formula:
Final Score = (Semantic Similarity * 0.40) + (Skill Match * 0.40) + (Experience Match * 0.20)
"""

import streamlit as st
import re
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

@st.cache_resource
def init_sentence_transformer():
    """
    Loads and caches the SentenceTransformer model.
    
    Returns:
        SentenceTransformer: The 'all-MiniLM-L6-v2' model for semantic embedding.
    """
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer('all-MiniLM-L6-v2')

def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculates the cosine similarity between two text strings using MiniLM embeddings.

    Args:
        text1 (str): First text string (e.g., candidate summary).
        text2 (str): Second text string (e.g., job description).

    Returns:
        float: Cosine similarity score between 0.0 and 1.0.
    """
    if not text1 or not text2:
        return 0.0
    model = init_sentence_transformer()
    embeddings = model.encode([text1, text2])
    score = cosine_similarity([embeddings[0]], [embeddings[1]])[0][0]
    return float(max(0.0, min(1.0, score)))

def _get_jd_required_years(jd_text: str) -> float:
    """
    Internal helper to extract the maximum 'years of experience' requirement from a JD.

    Args:
        jd_text (str): The raw text of the Job Description.

    Returns:
        float: The highest number found followed by 'years', or 0.0 if not found.
    """
    pattern = r'(\d+(?:\.\d+)?)\s*\+?\s*years?'
    matches = [float(y) for y in re.findall(pattern, jd_text.lower())]
    return max(matches) if matches else 0.0

def estimate_experience_score(total_years: float, jd_text: str) -> float:
    """
    Scores the candidate's total professional experience against the JD requirement.

    If JD has no requirement, returns a neutral 0.5 with a small weight for any experience.
    If requirement exists, applies a penalty if the candidate is below certain thresholds (tiers).

    Args:
        total_years (float): The candidate's pre-calculated total experience in years.
        jd_text (str): The raw text of the Job Description.

    Returns:
        float: A normalized experience score between 0.0 and 1.0.
    """
    req_years = _get_jd_required_years(jd_text)

    if req_years == 0:
        # JD has no explicit requirement → neutral 0.5
        if total_years > 0:
            # Bonus for having any experience
            return min(0.5 + (total_years / 20.0), 0.75)
        return 0.5

    if total_years == 0:
        return 0.05  # No dated experience found at all

    ratio = total_years / req_years
    if ratio >= 1.0:
        return 1.0
    elif ratio >= 0.8:
        return 0.85
    elif ratio >= 0.6:
        return 0.65
    elif ratio >= 0.4:
        return 0.40   # Below threshold — penalty applied
    elif ratio >= 0.2:
        return 0.20   # Significant penalty
    else:
        return 0.05   # Critical under-qualification

def calculate_skill_match_score(resume_skills: list, jd_skills: list) -> tuple:
    """
    Calculates the strict keyword intersection score between candidate and JD skills.

    Args:
        resume_skills (list): List of detected technical skills in the resume.
        jd_skills (list): List of target technical skills in the JD.

    Returns:
        tuple: (score_float, matched_list, gap_list) where score is intersection/total_jd.
    """
    res_set = set(s.lower().strip() for s in resume_skills)
    jd_set = set(s.lower().strip() for s in jd_skills)

    if not jd_set:
        return 0.0, [], []

    matched = sorted(list(res_set.intersection(jd_set)))
    gaps = sorted(list(jd_set.difference(res_set)))
    score = len(matched) / len(jd_set)
    return score, matched, gaps

def build_verdict(
    semantic: float, skill: float, experience: float,
    matched: list, gaps: list, total_years: float, req_years: float
) -> str:
    """
    Generates a descriptive, data-driven "System Verdict" for the recruiter.

    Args:
        semantic (float): The semantic context score.
        skill (float): The heuristic skill match score.
        experience (float): The calculated experience score.
        matched (list): List of matching skills.
        gaps (list): List of missing skills.
        total_years (float): Candidate's estimated years.
        req_years (float): JD's required years.

    Returns:
        str: A concatenated human-readable verdict.
    """
    sem_pct = semantic * 100
    skill_pct = skill * 100

    parts = []

    # Semantic alignment
    if sem_pct >= 65:
        parts.append("Strong contextual alignment with the job description")
    elif sem_pct >= 40:
        parts.append("Moderate contextual overlap with the position requirements")
    else:
        parts.append("Low semantic alignment — resume content diverges from the job description")

    # Skill coverage
    if skill_pct >= 60:
        parts.append(f"demonstrates solid skill coverage ({', '.join(matched[:3]) if matched else 'multiple areas'})")
    elif skill_pct >= 20:
        parts.append(f"shows partial skill match ({', '.join(matched[:2]) if matched else 'limited areas'})")
    else:
        parts.append("with minimal to no detectable skill intersection against JD requirements")

    # Gaps
    if gaps:
        parts.append(f"Key gaps flagged: {', '.join(gaps[:3])}")
    elif matched:
        parts.append("No critical skill gaps identified")

    # Experience narrative
    if req_years > 0:
        if total_years >= req_years:
            parts.append(f"experience ({total_years} yrs) meets the {req_years:.0f}-year requirement")
        else:
            shortfall = req_years - total_years
            parts.append(f"experience ({total_years} yrs) is {shortfall:.1f} years below the {req_years:.0f}-year requirement")
    else:
        if total_years > 0:
            parts.append(f"carries an estimated {total_years} years of professional experience")
        else:
            parts.append("no datable experience periods found in the resume")

    verdict = parts[0]
    if len(parts) > 1:
        verdict += f", {parts[1]}."
    if len(parts) > 2:
        verdict += f" {parts[2]}."
    if len(parts) > 3:
        verdict += f" Candidate {parts[3]}."
    return verdict

def rank_candidates(resumes_data: list, jd_text: str, jd_skills: list) -> pd.DataFrame:
    """
    The main integration function that scores multiple candidates against a JD.

    Args:
        resumes_data (list): List of dictionaries containing candidate text, name, etc.
        jd_text (str): The raw text of the Job Description.
        jd_skills (list): Pre-extracted skills from the JD.

    Returns:
        pd.DataFrame: A ranked DataFrame sorted by 'Final Score'.
    """
    results = []
    req_years = float(max([float(y) for y in re.findall(r'(\d+(?:\.\d+)?)\s*\+?\s*years?', jd_text.lower())] or [0]))

    for candidate in resumes_data:
        res_text = candidate['text']
        res_skills = candidate.get('skills', [])
        total_years = candidate.get('total_years', 0.0)
        entities = candidate.get('entities', {
            "technical_skills": res_skills,
            "professional_experience": [],
            "education": []
        })

        semantic_score = calculate_similarity(res_text, jd_text)
        skill_score, matched, gaps = calculate_skill_match_score(res_skills, jd_skills)
        exp_score = estimate_experience_score(total_years, jd_text)

        # Transparent formula: Semantic 40% + Skills 40% + Experience 20%
        final_score = (0.40 * semantic_score) + (0.40 * skill_score) + (0.20 * exp_score)

        verdict = build_verdict(semantic_score, skill_score, exp_score, matched, gaps, total_years, req_years)

        results.append({
            "Candidate File": candidate['name'],
            "Final Score": round(final_score * 100, 1),
            "Semantic Score": round(semantic_score * 100, 1),
            "Skill Match": round(skill_score * 100, 1),
            "Experience Match": round(exp_score * 100, 1),
            "Total Years": total_years,
            "Technical Skills": entities.get("technical_skills", []),
            "Professional Experience": entities.get("professional_experience", []),
            "Education": entities.get("education", []),
            "Matched Skills": matched,
            "Gap Skills": gaps,
            "Verdict": verdict,
            "File Bytes": candidate.get('file_bytes', b''),
            "File Name": candidate['name'],
        })

    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by="Final Score", ascending=False).reset_index(drop=True)
    return df
