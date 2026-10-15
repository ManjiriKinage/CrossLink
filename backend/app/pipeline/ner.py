import spacy
import re
from typing import List, Dict, Any
from app.pipeline.canonicalizer import canonicalize_entity, is_valid_entity
from app.config import settings

_nlp = None

def get_nlp():
    """
    Lazy loads and returns the spaCy model.
    """
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load(settings.SPACY_MODEL)
        except OSError:
            from spacy.cli import download
            download(settings.SPACY_MODEL)
            _nlp = spacy.load(settings.SPACY_MODEL)
    return _nlp

ENTITY_TYPE_MAPPING = {
    "PERSON": "PERSON",
    "GPE": "LOCATION",
    "LOC": "LOCATION",
    "FAC": "LOCATION",
    "ORG": "ORGANIZATION",
    "DATE": "DATE",
    "TIME": "DATE",
    "PRODUCT": "ARTIFACT",
    "WORK_OF_ART": "ARTIFACT"
}

STOP_ENTITIES = {
    "the", "a", "an", "this", "that", "it", "today", "yesterday", "tomorrow",
    "night", "morning", "afternoon", "evening", "hours", "days", "months",
    "inr", "rs", "usd", "cfo", "ceo", "director", "general counsel", "auditor",
    "date", "time", "interviewer", "interviewee", "subject", "from", "to", "regards"
}

ARTIFACT_KEYWORDS = {
    "sapphire", "diamond", "gemstone", "ruby", "emerald", "jewelry",
    "artifact", "painting", "sculpture", "relic", "manuscript"
}

def extract_entities(text: str) -> List[Dict[str, Any]]:
    """
    Extracts, normalizes, and filters named entities from text using spaCy.
    General and case-agnostic.
    """
    if not text:
        return []
        
    nlp = get_nlp()
    doc = nlp(text)
    
    entities = []
    seen = set()
    
    for ent in doc.ents:
        raw_name = " ".join(ent.text.replace("\n", " ").split()).strip()
        if len(raw_name) < 2:
            continue
            
        mapped_type = ENTITY_TYPE_MAPPING.get(ent.label_, "UNKNOWN")
        if mapped_type == "UNKNOWN":
            continue
            
        if raw_name.lower() in STOP_ENTITIES:
            continue

        if not is_valid_entity(raw_name, mapped_type):
            continue
            
        # Clean canonical form
        canonical = canonicalize_entity(raw_name, mapped_type)
        if not is_valid_entity(canonical, mapped_type):
            continue

        # Check if entity refers to a physical artifact
        if any(ak in canonical.lower() for ak in ARTIFACT_KEYWORDS):
            mapped_type = "ARTIFACT"

        # Deduplicate per chunk
        unique_key = (canonical, mapped_type)
        if unique_key in seen:
            continue
        seen.add(unique_key)
        
        entities.append({
            "name": raw_name,
            "canonical_name": canonical,
            "type": mapped_type,
            "start_char": ent.start_char,
            "end_char": ent.end_char
        })

    # Also detect key artifact full references if spaCy split or missed them
    # E.g., "Blue Sapphire of Maratha"
    for m in re.finditer(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Sapphire|Diamond|Gemstone|Jewel)(?:\s+of\s+[A-Z][a-z]+)?)\b", text):
        art_name = m.group(1).strip()
        canon_art = canonicalize_entity(art_name, "ARTIFACT")
        if is_valid_entity(canon_art, "ARTIFACT"):
            unique_key = (canon_art, "ARTIFACT")
            if unique_key not in seen:
                seen.add(unique_key)
                entities.append({
                    "name": art_name,
                    "canonical_name": canon_art,
                    "type": "ARTIFACT",
                    "start_char": m.start(),
                    "end_char": m.end()
                })
        
    return entities
