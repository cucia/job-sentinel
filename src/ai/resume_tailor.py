"""
Resume Tailoring Module

Dynamically tailors resume to highlight relevant skills and experience for each job.
Includes keyword dominance logic for ATS optimization.
"""

import os
import json
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from collections import Counter


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
                "relevance_score": 0-100,
                "keyword_density": float,
                "critical_keywords": [str]
            }
        """
        # Extract job requirements
        job_title = job.get("title", "")
        job_description = job.get("description", "")
        company = job.get("company", "unknown")

        # Extract critical keywords (keyword dominance logic)
        critical_keywords = self._extract_critical_keywords(job_title, job_description)

        # Analyze job requirements
        required_skills = self._extract_required_skills(job_description)
        key_keywords = self._extract_keywords(job_title, job_description)

        # Tailor components with keyword optimization
        tailored_skills = self._tailor_skills(required_skills, critical_keywords)
        tailored_projects = self._reorder_projects(required_skills, key_keywords, critical_keywords)
        tailored_summary = self._tailor_summary(job_title, required_skills, critical_keywords)
        keyword_alignment = self._align_keywords(key_keywords)

        # Optimize experience section with keywords
        tailored_experience = self._optimize_experience(self.profile.get("experience", ""), critical_keywords)

        # Build tailored content
        tailored_content = {
            "name": self.profile.get("name", ""),
            "email": self.profile.get("email", ""),
            "phone": self.profile.get("phone", ""),
            "summary": tailored_summary,
            "skills": tailored_skills,
            "experience": tailored_experience,
            "projects": tailored_projects,
            "education": self.profile.get("education", ""),
            "keywords": keyword_alignment,
            "critical_keywords": critical_keywords,
            "tailored_for": {
                "job_title": job_title,
                "company": company,
                "date": datetime.now().isoformat(),
            }
        }

        # Track changes
        changes_made = self._track_changes(tailored_skills, tailored_projects, tailored_summary, critical_keywords)

        # Calculate relevance score
        relevance_score = self._calculate_relevance(required_skills, tailored_skills, key_keywords)

        # Calculate keyword density
        keyword_density = self._calculate_keyword_density(tailored_content, critical_keywords)

        # Save tailored resume
        resume_path = self._save_tailored_resume(tailored_content, company, job_title)

        return {
            "resume_path": resume_path,
            "tailored_content": tailored_content,
            "changes_made": changes_made,
            "relevance_score": relevance_score,
            "keyword_density": keyword_density,
            "critical_keywords": critical_keywords,
        }

    def _extract_critical_keywords(self, title: str, description: str) -> List[str]:
        """
        Extract top 5-10 critical keywords from job posting.
        Uses frequency analysis and position weighting.

        Returns: List of critical keywords
        """
        text = f"{title} {description}".lower()

        # Common stop words to exclude
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
            "been", "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "should", "could", "may", "might", "must", "can", "this",
            "that", "these", "those", "we", "you", "they", "our", "your", "their"
        }

        # Extract words and phrases
        words = re.findall(r'\b[a-z]{3,}\b', text)

        # Count frequency
        word_freq = Counter(words)

        # Remove stop words
        filtered_freq = {word: count for word, count in word_freq.items()
                        if word not in stop_words and count >= 2}

        # Boost keywords that appear in title
        title_lower = title.lower()
        for word in filtered_freq:
            if word in title_lower:
                filtered_freq[word] *= 3

        # Extract technical terms and skills from profile
        profile_skills = [s.lower() for s in self.profile.get("skills", [])]
        profile_keywords = [k.lower() for k in self.profile.get("keywords", [])]

        # Boost profile-matching keywords
        for word in filtered_freq:
            if word in profile_skills or word in profile_keywords:
                filtered_freq[word] *= 2

        # Get top keywords
        top_keywords = sorted(filtered_freq.items(), key=lambda x: x[1], reverse=True)

        # Extract 2-word phrases (bigrams) for technical terms
        bigrams = []
        words_list = text.split()
        for i in range(len(words_list) - 1):
            bigram = f"{words_list[i]} {words_list[i+1]}"
            # Only include if both words are meaningful
            if (words_list[i] not in stop_words and
                words_list[i+1] not in stop_words and
                len(words_list[i]) >= 3 and len(words_list[i+1]) >= 3):
                bigrams.append(bigram)

        bigram_freq = Counter(bigrams)
        top_bigrams = [bg for bg, count in bigram_freq.most_common(3) if count >= 2]

        # Combine single words and bigrams
        critical = [word for word, count in top_keywords[:8]]
        critical.extend(top_bigrams)

        # Limit to 10 keywords
        return critical[:10]

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

    def _tailor_skills(self, required_skills: List[str], critical_keywords: List[str] = None) -> List[str]:
        """
        Reorder skills to prioritize required ones and critical keywords.

        Returns: Reordered skill list
        """
        critical_keywords = critical_keywords or []
        all_skills = self.profile.get("skills", [])
        all_skills_lower = [s.lower() for s in all_skills]

        # Separate into priority tiers
        tier1_critical = []  # Required skills + critical keywords
        tier2_relevant = []  # Other relevant skills
        tier3_other = []     # Remaining skills

        for skill in all_skills:
            skill_lower = skill.lower()
            if skill_lower in required_skills or any(kw in skill_lower for kw in critical_keywords):
                tier1_critical.append(skill)
            elif any(kw in skill_lower for kw in critical_keywords):
                tier2_relevant.append(skill)
            else:
                tier3_other.append(skill)

        # Return prioritized order
        return tier1_critical + tier2_relevant + tier3_other

    def _reorder_projects(self, required_skills: List[str], keywords: List[str], critical_keywords: List[str] = None) -> List[dict]:
        """
        Reorder projects to highlight most relevant ones.
        Enhanced with critical keyword matching.

        Returns: Reordered project list
        """
        critical_keywords = critical_keywords or []
        projects = self.profile.get("projects", [])
        if not projects:
            return []

        # Score each project by relevance
        scored_projects = []
        for project in projects:
            score = self._score_project_relevance(project, required_skills, keywords, critical_keywords)
            scored_projects.append((score, project))

        # Sort by score (descending)
        scored_projects.sort(key=lambda x: x[0], reverse=True)

        # Return reordered projects
        return [proj for score, proj in scored_projects]

    def _score_project_relevance(self, project: dict, required_skills: List[str], keywords: List[str], critical_keywords: List[str] = None) -> int:
        """Score project relevance to job with critical keyword boost."""
        critical_keywords = critical_keywords or []
        score = 0
        project_text = f"{project.get('name', '')} {project.get('description', '')}".lower()

        # Check for critical keywords (highest priority)
        for keyword in critical_keywords:
            if keyword in project_text:
                score += 5

        # Check for required skills
        for skill in required_skills:
            if skill in project_text:
                score += 3

        # Check for keywords
        for keyword in keywords:
            if keyword in project_text:
                score += 2

        return score

    def _tailor_summary(self, job_title: str, required_skills: List[str], critical_keywords: List[str] = None) -> str:
        """
        Tailor professional summary to match job with critical keywords.
        Ensures natural integration of keywords.

        Returns: Tailored summary text
        """
        critical_keywords = critical_keywords or []
        base_summary = self.profile.get("summary", "")
        role = self.profile.get("role", "")

        # Select top 3 critical keywords that aren't already in summary
        base_lower = base_summary.lower()
        missing_keywords = [kw for kw in critical_keywords[:5] if kw not in base_lower][:3]

        # If no base summary, generate one with keywords
        if not base_summary:
            top_skills = ", ".join(required_skills[:3]) if required_skills else "various technologies"
            keyword_phrase = f" including {', '.join(missing_keywords)}" if missing_keywords else ""
            return f"{role} with expertise in {top_skills}{keyword_phrase}, seeking opportunities in {job_title}."

        # Enhance existing summary with critical keywords naturally
        if missing_keywords:
            # Add keywords in a natural way
            keyword_integration = f" Specialized in {', '.join(missing_keywords[:2])}"
            if len(missing_keywords) > 2:
                keyword_integration += f" and {missing_keywords[2]}"
            enhanced = f"{base_summary}{keyword_integration} with focus on {job_title} roles."
            return enhanced
        elif required_skills:
            # Fallback to required skills if keywords already present
            top_skills = ", ".join(required_skills[:3])
            enhanced = f"{base_summary} Specialized in {top_skills} with focus on {job_title} roles."
            return enhanced

        return base_summary

    def _optimize_experience(self, experience: str, critical_keywords: List[str]) -> str:
        """
        Optimize experience section with critical keywords.
        Maintains natural structure while increasing keyword density.

        Returns: Optimized experience text
        """
        if not experience or not critical_keywords:
            return experience

        # Check which keywords are missing
        experience_lower = experience.lower()
        missing_keywords = [kw for kw in critical_keywords[:5] if kw not in experience_lower]

        # If all keywords present, return as-is
        if not missing_keywords:
            return experience

        # Add a natural bullet point with missing keywords
        # This maintains structure without spamming
        keyword_phrase = ", ".join(missing_keywords[:3])
        additional_point = f"\n• Applied expertise in {keyword_phrase} to deliver technical solutions"

        return experience + additional_point

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

    def _track_changes(self, tailored_skills: List[str], tailored_projects: List[dict], tailored_summary: str, critical_keywords: List[str]) -> List[str]:
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

        # Track keyword optimization
        if critical_keywords:
            changes.append(f"Optimized for {len(critical_keywords)} critical keywords")

        return changes

    def _calculate_keyword_density(self, content: dict, critical_keywords: List[str]) -> float:
        """
        Calculate keyword density in tailored resume.

        Returns: Keyword density percentage (0-100)
        """
        if not critical_keywords:
            return 0.0

        # Combine all text content
        text_parts = [
            content.get("summary", ""),
            " ".join(content.get("skills", [])),
            content.get("experience", ""),
        ]

        # Add project descriptions
        for project in content.get("projects", []):
            text_parts.append(project.get("name", ""))
            text_parts.append(project.get("description", ""))

        full_text = " ".join(text_parts).lower()

        # Count keyword occurrences
        total_occurrences = 0
        for keyword in critical_keywords:
            total_occurrences += full_text.count(keyword.lower())

        # Calculate density (occurrences per 100 words)
        word_count = len(full_text.split())
        if word_count == 0:
            return 0.0

        density = (total_occurrences / word_count) * 100
        return round(density, 2)

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
