"""
Resume Parser for Job Sentinel

Extracts structured data from resume files (PDF, DOCX, TXT).
Uses regex + basic NLP with optional LLM enhancement.
"""

import re
import os
from typing import Optional


def _extract_text_from_pdf(file_path: str) -> str:
    """Extract text from PDF file."""
    try:
        import PyPDF2
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text
    except ImportError:
        raise RuntimeError("PyPDF2 not installed. Run: pip install PyPDF2")
    except Exception as e:
        raise RuntimeError(f"Failed to extract PDF text: {e}")


def _extract_text_from_docx(file_path: str) -> str:
    """Extract text from DOCX file."""
    try:
        import docx
        doc = docx.Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])
    except ImportError:
        raise RuntimeError("python-docx not installed. Run: pip install python-docx")
    except Exception as e:
        raise RuntimeError(f"Failed to extract DOCX text: {e}")


def _extract_text_from_txt(file_path: str) -> str:
    """Extract text from TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        raise RuntimeError(f"Failed to read TXT file: {e}")


def _extract_text(file_path: str) -> str:
    """Extract text from resume file based on extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return _extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return _extract_text_from_docx(file_path)
    elif ext == '.txt':
        return _extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use PDF, DOCX, or TXT.")


def _extract_email(text: str) -> Optional[str]:
    """Extract email address."""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    matches = re.findall(pattern, text)
    return matches[0] if matches else None


def _extract_phone(text: str) -> Optional[str]:
    """Extract phone number."""
    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\d{10}',
        r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}'
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        if matches:
            return matches[0].strip()
    return None


def _extract_name(text: str) -> Optional[str]:
    """Extract name (first line heuristic)."""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    if not lines:
        return None
    first_line = lines[0]
    if len(first_line.split()) <= 4 and not re.search(r'[@\d]', first_line):
        return first_line
    return None


def _extract_skills(text: str) -> list[str]:
    """Extract skills using keyword matching."""
    skill_section_pattern = r'(?:skills?|technical skills?|core competencies)[:\s]+(.*?)(?:\n\n|\n[A-Z]|$)'
    match = re.search(skill_section_pattern, text, re.IGNORECASE | re.DOTALL)

    if match:
        skills_text = match.group(1)
        skills = re.split(r'[,;|\n•·]', skills_text)
        return [s.strip() for s in skills if s.strip() and len(s.strip()) > 2][:15]

    common_skills = [
        'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker',
        'kubernetes', 'git', 'agile', 'machine learning', 'data analysis', 'api',
        'rest', 'graphql', 'mongodb', 'postgresql', 'redis', 'ci/cd', 'jenkins'
    ]
    found_skills = []
    text_lower = text.lower()
    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill.title())
    return found_skills[:10]


def _extract_experience(text: str) -> Optional[str]:
    """Extract total years of experience."""
    patterns = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'experience[:\s]+(\d+)\+?\s*years?',
        r'(\d+)\+?\s*yrs?\s+(?:of\s+)?experience'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            years = match.group(1)
            return f"{years} years"
    return None


def _extract_education(text: str) -> Optional[str]:
    """Extract education degree."""
    degrees = [
        r'(?:bachelor|b\.?s\.?|b\.?tech|b\.?e\.?)',
        r'(?:master|m\.?s\.?|m\.?tech|mba)',
        r'(?:phd|ph\.?d\.?|doctorate)'
    ]
    for degree_pattern in degrees:
        match = re.search(degree_pattern, text, re.IGNORECASE)
        if match:
            line_start = max(0, match.start() - 50)
            line_end = min(len(text), match.end() + 50)
            context = text[line_start:line_end].strip()
            return context.split('\n')[0][:100]
    return None


def _extract_linkedin(text: str) -> Optional[str]:
    """Extract LinkedIn URL."""
    pattern = r'(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else None


def _extract_github(text: str) -> Optional[str]:
    """Extract GitHub URL."""
    pattern = r'(?:https?://)?(?:www\.)?github\.com/[\w-]+'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(0) if match else None


def _parse_with_regex(text: str) -> dict:
    """Parse resume using regex patterns."""
    return {
        "name": _extract_name(text),
        "email": _extract_email(text),
        "phone": _extract_phone(text),
        "skills": _extract_skills(text),
        "experience": _extract_experience(text),
        "education": _extract_education(text),
        "linkedin_url": _extract_linkedin(text),
        "github_url": _extract_github(text),
    }


def _parse_with_llm(text: str) -> dict:
    """Parse resume using LLM for better extraction."""
    try:
        from src.ai.cloud_llm import CloudLLMClient

        api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return {}

        provider = "groq" if os.environ.get("GROQ_API_KEY") else "openai"
        client = CloudLLMClient(provider=provider)

        prompt = f"""Extract structured information from this resume. Return ONLY valid JSON with these exact keys:
{{
  "name": "full name",
  "email": "email address",
  "phone": "phone number",
  "skills": ["skill1", "skill2", ...],
  "experience": "X years",
  "education": "highest degree",
  "linkedin_url": "linkedin profile url",
  "github_url": "github profile url",
  "current_company": "current employer",
  "role": "current job title"
}}

If a field is not found, use null. Do not add any explanation, only return the JSON.

Resume text:
{text[:3000]}"""

        messages = [{"role": "user", "content": prompt}]
        response = client.chat(messages, temperature=0.1)

        import json
        response_clean = response.strip()
        if response_clean.startswith("```json"):
            response_clean = response_clean[7:]
        if response_clean.startswith("```"):
            response_clean = response_clean[3:]
        if response_clean.endswith("```"):
            response_clean = response_clean[:-3]

        parsed = json.loads(response_clean.strip())
        return {k: v for k, v in parsed.items() if v is not None}
    except Exception:
        return {}


def parse_resume(file_path: str) -> dict:
    """Parse resume file and extract structured data."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Resume file not found: {file_path}")

    text = _extract_text(file_path)

    llm_data = _parse_with_llm(text)
    if llm_data:
        regex_data = _parse_with_regex(text)
        for key, value in regex_data.items():
            if key not in llm_data or not llm_data[key]:
                llm_data[key] = value
        return llm_data

    return _parse_with_regex(text)
