"""
Resume Tailoring Module

Dynamically tailors resume to highlight relevant skills and experience for each job.
"""

import os
import json
from typing import Dict, List, Optional
from datetime import datetime


class ResumeTailor:
    """Tailors resume content to match job requirements."""

    def __init__(self, profile: dict):
        self.profile = profile
        self.tailored_resumes_dir = "data/tailored_resumes"
        os.makedirs(self.tailored_resumes_dir, exist_ok=True)

    def tailor_resume(self, job: dict) -> dict:
        """
        Tailor resume for specific job.

        Args:
            job: Job details

        Returns:
            {
                "resume_path": str,
                "tailored_content": dict,
                "changes_made": [str],
                "relevance_score": 0-100
            }
        """
        # Extract job requirements
        job_title = job.get("title", "")
        job_description = job.get("description", "")
        company = job.get("company", "unknown")

        # Analyze job requirements
        required_skills = self._extract_required_skills(job_description)
        key_keywords = self._extract_keywords(job_title, job_description)

        # Tailor components
        tailored_skills = self._tailor_skills(required_skills)
        tailored_projects = self._reorder_projects(required_skills, key_keywords)
        tailored_summary = self._tailor_summary(job_title, required_skills)
        keyword_alignment = self._align_keywords(key_keywords)

        # Build tailored content
        tailored_content = {
            "name": self.profile.get("name", ""),
            "email": self.profile.get("email", ""),
            "phone": self.profile.get("phone", ""),
            "summary": tailored_summary,
            "skills": tailored_skills,
            "experience": self.profile.get("experience", ""),
            "projects": tailored_projects,
            "education": self.profile.get("education", ""),
            "keywords": keyword_alignment,
            "tailored_for": {
                "job_title": job_title,
                "company": company,
                "date": datetime.now().isoformat(),
            }
        }

        # Track changes
        changes_made = self._track_changes(tailored_skills, tailored_projects, tailored_summary)

        # Calculate relevance score
        relevance_score = self._calculate_relevance(required_skills, tailored_skills, key_keywords)

        # Save tailored resume
        resume_path = self._save_tailored_resume(tailored_content, company, job_title)

        return {
            "resume_path": resume_path,
            "tailored_content": tailored_content,
            "changes_made": changes_made,
            "relevance_score": relevance_score,
        }

    def _extract_required_skills(self, description: str) -> List[str]:
        """Extract required skills from job description."""
        description_lower = description.lower()
        profile_skills = [s.lower() for s in self.profile.get("skills", [])]

        # Find skills mentioned in job description
        required = []
        for skill in profile_skills:
            if skill in description_lower:
                required.append(skill)

        return required

    def _extract_keywords(self, title: str, description: str) -> List[str]:
        """Extract key keywords from job posting."""
        text = f"{title} {description}".lower()
        profile_keywords = [k.lower() for k in self.profile.get("keywords", [])]

        # Find keywords mentioned in job
        relevant = []
        for keyword in profile_keywords:
            if keyword in text:
                relevant.append(keyword)

        return relevant

    def _tailor_skills(self, required_skills: List[str]) -> List[str]:
        """
        Reorder skills to prioritize required ones.

        Returns: Reordered skill list
        """
        all_skills = self.profile.get("skills", [])
        all_skills_lower = [s.lower() for s in all_skills]

        # Separate required and other skills
        prioritized = []
        other = []

        for skill in all_skills:
            if skill.lower() in required_skills:
                prioritized.append(skill)
            else:
                other.append(skill)

        # Return prioritized first, then others
        return prioritized + other

    def _reorder_projects(self, required_skills: List[str], keywords: List[str]) -> List[dict]:
        """
        Reorder projects to highlight most relevant ones.

        Returns: Reordered project list
        """
        projects = self.profile.get("projects", [])
        if not projects:
            return []

        # Score each project by relevance
        scored_projects = []
        for project in projects:
            score = self._score_project_relevance(project, required_skills, keywords)
            scored_projects.append((score, project))

        # Sort by score (descending)
        scored_projects.sort(key=lambda x: x[0], reverse=True)

        # Return reordered projects
        return [proj for score, proj in scored_projects]

    def _score_project_relevance(self, project: dict, required_skills: List[str], keywords: List[str]) -> int:
        """Score project relevance to job."""
        score = 0
        project_text = f"{project.get('name', '')} {project.get('description', '')}".lower()

        # Check for required skills
        for skill in required_skills:
            if skill in project_text:
                score += 3

        # Check for keywords
        for keyword in keywords:
            if keyword in project_text:
                score += 2

        return score

    def _tailor_summary(self, job_title: str, required_skills: List[str]) -> str:
        """
        Tailor professional summary to match job.

        Returns: Tailored summary text
        """
        base_summary = self.profile.get("summary", "")
        role = self.profile.get("role", "")

        # If no base summary, generate one
        if not base_summary:
            top_skills = ", ".join(required_skills[:3]) if required_skills else "various technologies"
            return f"{role} with expertise in {top_skills}, seeking opportunities in {job_title}."

        # Enhance existing summary with job-specific keywords
        if required_skills:
            top_skills = ", ".join(required_skills[:3])
            enhanced = f"{base_summary} Specialized in {top_skills} with focus on {job_title} roles."
            return enhanced

        return base_summary

    def _align_keywords(self, key_keywords: List[str]) -> List[str]:
        """
        Align profile keywords with job keywords.

        Returns: Prioritized keyword list
        """
        all_keywords = self.profile.get("keywords", [])
        all_keywords_lower = [k.lower() for k in all_keywords]

        # Prioritize job-relevant keywords
        prioritized = []
        other = []

        for keyword in all_keywords:
            if keyword.lower() in key_keywords:
                prioritized.append(keyword)
            else:
                other.append(keyword)

        return prioritized + other

    def _track_changes(self, tailored_skills: List[str], tailored_projects: List[dict], tailored_summary: str) -> List[str]:
        """Track what changes were made."""
        changes = []

        # Check skill reordering
        original_skills = self.profile.get("skills", [])
        if tailored_skills != original_skills:
            changes.append("Reordered skills to prioritize job requirements")

        # Check project reordering
        original_projects = self.profile.get("projects", [])
        if tailored_projects != original_projects:
            changes.append("Reordered projects to highlight relevant experience")

        # Check summary changes
        original_summary = self.profile.get("summary", "")
        if tailored_summary != original_summary:
            changes.append("Enhanced summary with job-specific keywords")

        return changes

    def _calculate_relevance(self, required_skills: List[str], tailored_skills: List[str], keywords: List[str]) -> int:
        """
        Calculate relevance score of tailored resume.

        Returns: 0-100 score
        """
        score = 0

        # Skill coverage (50% weight)
        if required_skills:
            skill_coverage = len(required_skills) / len(tailored_skills) if tailored_skills else 0
            score += min(50, skill_coverage * 50)

        # Keyword coverage (30% weight)
        profile_keywords = self.profile.get("keywords", [])
        if keywords and profile_keywords:
            keyword_coverage = len(keywords) / len(profile_keywords)
            score += min(30, keyword_coverage * 30)

        # Project relevance (20% weight)
        projects = self.profile.get("projects", [])
        if projects:
            relevant_projects = sum(1 for p in projects if self._score_project_relevance(p, required_skills, keywords) > 0)
            project_score = (relevant_projects / len(projects)) * 20
            score += project_score

        return int(min(100, score))

    def _save_tailored_resume(self, content: dict, company: str, job_title: str) -> str:
        """Save tailored resume to file."""
        # Create safe filename
        safe_company = "".join(c for c in company if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).strip()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_company}_{safe_title}_{timestamp}.json"
        filepath = os.path.join(self.tailored_resumes_dir, filename)

        # Save as JSON
        with open(filepath, 'w') as f:
            json.dump(content, f, indent=2)

        return filepath


def tailor_resume(profile: dict, job: dict) -> dict:
    """
    Convenience function to tailor resume.

    Args:
        profile: Candidate profile
        job: Job details

    Returns:
        Tailoring result dict
    """
    tailor = ResumeTailor(profile)
    return tailor.tailor_resume(job)
