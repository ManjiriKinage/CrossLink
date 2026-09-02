import re
from typing import List, Dict, Any, Tuple

def extract_sentences(text: str) -> List[str]:
    """
    Splits text into sentences.
    """
    # Simple regex sentence splitting
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def extract_cooccurrences(
    chunk_id: int,
    document_name: str,
    chunk_text: str,
    entities: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Discovers co-occurring entity pairs within a chunk.
    Calculates edge weights (higher weight if co-occurring in the exact same sentence).
    Captures the verbatim sentence/snippet as evidence.
    """
    if len(entities) < 2:
        return []
        
    sentences = extract_sentences(chunk_text)
    cooccurrences = []
    
    # Generate all unique entity pairs
    n = len(entities)
    for i in range(n):
        for j in range(i + 1, n):
            ent_a = entities[i]
            ent_b = entities[j]
            
            canonical_a = ent_a["canonical_name"]
            canonical_b = ent_b["canonical_name"]
            
            # Avoid self-loops
            if canonical_a.lower() == canonical_b.lower():
                continue
                
            # Order deterministically
            if canonical_a > canonical_b:
                source, target = canonical_b, canonical_a
                source_type, target_type = ent_b["type"], ent_a["type"]
            else:
                source, target = canonical_a, canonical_b
                source_type, target_type = ent_a["type"], ent_b["type"]
                
            # Find evidence sentence(s)
            matching_sentences = []
            for sent in sentences:
                sent_lower = sent.lower()
                # Check if both raw or canonical or sub-names appear in this sentence
                name_a = ent_a["name"].lower()
                name_b = ent_b["name"].lower()
                can_a = canonical_a.lower()
                can_b = canonical_b.lower()
                
                has_a = (name_a in sent_lower) or (can_a in sent_lower)
                has_b = (name_b in sent_lower) or (can_b in sent_lower)
                
                if has_a and has_b:
                    matching_sentences.append(sent)
                    
            if matching_sentences:
                # Same-sentence co-occurrence gives higher weight
                weight = 2.0
                snippet = " ... ".join(matching_sentences)
            else:
                # Same-chunk co-occurrence
                weight = 1.0
                snippet = chunk_text[:350].strip() + ("..." if len(chunk_text) > 350 else "")
                
            cooccurrences.append({
                "chunk_id": chunk_id,
                "document_name": document_name,
                "source_entity": source,
                "source_type": source_type,
                "target_entity": target,
                "target_type": target_type,
                "relationship_type": "CO_OCCURRED_IN",
                "snippet_text": snippet,
                "weight": weight
            })
            
    return cooccurrences
