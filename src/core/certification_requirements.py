"""
Certification Requirements Module
Loads and validates certification requirements from JSON configuration.
"""
import json
import os
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SectionRequirement(BaseModel):
    """Certification requirement for a single section."""
    name: str
    required_keywords: List[str]
    scoring_weight: int = Field(ge=1, le=100)
    example_chunk_ids: List[str] = []
    validation_notes: str = ""


class CertificationRequirements(BaseModel):
    """Full certification requirements configuration."""
    version: str
    last_updated: str
    source_manual: str
    sections: Dict[str, SectionRequirement]
    disclaimer: str


class RequirementsLoader:
    """Loads and caches certification requirements."""
    
    _instance: Optional["RequirementsLoader"] = None
    _requirements: Optional[CertificationRequirements] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load(self, config_path: Optional[str] = None) -> CertificationRequirements:
        """Load requirements from JSON file. Cached after first load."""
        if self._requirements is not None:
            return self._requirements
        
        if config_path is None:
            # Default path relative to this file
            config_path = os.path.join(
                os.path.dirname(__file__),
                "..", "data", "certification_requirements.json"
            )
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        self._requirements = CertificationRequirements.model_validate(data)
        return self._requirements
    
    def get_section(self, section_id: str) -> Optional[SectionRequirement]:
        """Get requirements for a specific section."""
        reqs = self.load()
        return reqs.sections.get(section_id)
    
    def check_keywords(self, section_id: str, text: str) -> Dict[str, bool]:
        """Check which required keywords are present in text.
        
        Uses normalized text matching to handle PDF extraction issues
        (whitespace, line breaks, character variations).
        """
        section = self.get_section(section_id)
        if not section:
            return {}
        
        # Normalize text: remove extra whitespace, newlines, and common PDF artifacts
        import re
        normalized_text = re.sub(r'\s+', '', text)  # Remove all whitespace for matching
        normalized_text_spaced = re.sub(r'\s+', ' ', text)  # Normalize to single spaces
        
        results = {}
        for keyword in section.required_keywords:
            # Try multiple matching strategies
            normalized_keyword = re.sub(r'\s+', '', keyword)
            
            # Strategy 1: Exact match in original text
            if keyword in text:
                results[keyword] = True
            # Strategy 2: Match in whitespace-removed text
            elif normalized_keyword in normalized_text:
                results[keyword] = True
            # Strategy 3: Match in space-normalized text
            elif keyword in normalized_text_spaced:
                results[keyword] = True
            # Strategy 4: Partial keyword match (for compound words broken by line breaks)
            elif len(keyword) >= 2:
                # Check if all characters of keyword appear in order
                pattern = '.*'.join(list(keyword))
                if re.search(pattern, normalized_text_spaced[:5000]):  # Limit search for performance
                    results[keyword] = True
                else:
                    results[keyword] = False
            else:
                results[keyword] = False
        
        return results

    
    def calculate_section_score(self, section_id: str, text: str) -> int:
        """Calculate score for a section based on keyword presence."""
        section = self.get_section(section_id)
        if not section:
            return 0
        
        keyword_results = self.check_keywords(section_id, text)
        if not keyword_results:
            return 0
        
        # Score = (keywords found / total keywords) * weight
        found_count = sum(keyword_results.values())
        total_count = len(keyword_results)
        
        return int((found_count / total_count) * section.scoring_weight)
    
    def get_disclaimer(self) -> str:
        """Get the disclaimer text."""
        return self.load().disclaimer


# Singleton instance
requirements_loader = RequirementsLoader()
