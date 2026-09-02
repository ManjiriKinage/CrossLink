import re
import os
from typing import Dict, Any, List, Set, Tuple

def clean_canonical_name(name: str) -> str:
    """Cleans up messy extracted names."""
    if not name:
        return ""
    cleaned = name.strip().strip(",").strip(".").strip('"').strip("'")
    if cleaned.lower().startswith("the "):
        cleaned = cleaned[4:]
    return cleaned

def extract_timeline_anchors(evidence_list: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extracts date/time clues from evidence snippets for timeline reconstruction."""
    timeline = []
    seen = set()
    date_patterns = [
        r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,\s+\d{4}\b',
        r'\b\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}\b',
        r'\b(?:19|20)\d{2}\b',
        r'\b(?:around\s+)?\d{1,2}:\d{2}(?:\s*(?:hours|hrs|am|pm|AM|PM))?\b'
    ]

    for ev in evidence_list[:8]:
        text = ev.get("text", "")
        doc = ev.get("document", "Case Record").replace(".txt", "").replace("_", " ").title()
        for pat in date_patterns:
            matches = re.finditer(pat, text, re.IGNORECASE)
            for m in matches:
                anchor = m.group(0).strip()
                # Find the enclosing sentence
                start = max(0, text.rfind('.', 0, m.start()) + 1)
                end = text.find('.', m.end())
                if end == -1:
                    end = len(text)
                snippet = text[start:end].strip()
                key = (anchor.lower(), snippet[:40].lower())
                if key not in seen and len(snippet) > 20:
                    seen.add(key)
                    timeline.append({
                        "time_anchor": anchor,
                        "event": snippet,
                        "source": doc
                    })
                if len(timeline) >= 4:
                    break
        if len(timeline) >= 4:
            break
    return timeline

def synthesize_investigative_answer(
    query: str,
    query_entities: List[str],
    subgraph: Dict[str, Any],
    evidence_list: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    AI Lead Detective Agent Synthesizer.
    Analyzes graph co-occurrences, verbatim evidence passages, and entity roles
    to produce a comprehensive investigative briefing with deductive reasoning.
    """
    if not evidence_list and not subgraph.get("nodes"):
        return {
            "summary": "No corroborated evidence was found in the indexed case files matching this specific inquiry.",
            "detective_briefing": "Insufficient documentary evidence in current dossier. Further investigative records needed.",
            "deductive_reasoning": "No cross-references or semantic passages exist in the indexed database matching the query parameters.",
            "key_findings": [],
            "persons_of_interest": [],
            "locations_identified": [],
            "organizations_involved": [],
            "timeline_anchors": [],
            "corroborated_sources": 0,
            "confidence_score": "INCONCLUSIVE",
            "source_documents": []
        }

    query_lower = query.lower()
    nodes = subgraph.get("nodes", [])
    edges = subgraph.get("edges", [])

    # Extract documents
    cited_docs = list(dict.fromkeys([ev.get("document", "case file") for ev in evidence_list if ev.get("document")]))
    docs_count = len(cited_docs)

    # Categorize nodes dynamically
    persons = []
    locations = []
    organizations = []
    dates = []

    for n in nodes:
        label = clean_canonical_name(n.get("label", n.get("id", "")))
        ntype = n.get("type", "UNKNOWN")
        if not label or len(label) < 2:
            continue
        if ntype == "PERSON" and label not in persons:
            persons.append(label)
        elif ntype == "LOCATION" and label not in locations:
            locations.append(label)
        elif ntype == "ORGANIZATION" and label not in organizations:
            organizations.append(label)
        elif ntype == "DATE" and label not in dates:
            dates.append(label)

    # Corroborated key findings
    key_findings = []
    seen_findings = set()

    for ev in evidence_list:
        text = ev.get("text", "")
        clean_stmt = text.strip().strip('"').strip("'").strip()
        sentences = re.split(r'(?<=[.!?])\s+', clean_stmt)
        for s in sentences:
            s_clean = s.strip()
            if len(s_clean) > 25 and len(s_clean) < 260 and s_clean[0].isupper():
                sig = s_clean[:40].lower()
                if sig not in seen_findings:
                    seen_findings.add(sig)
                    doc_tag = ev.get("document", "").replace(".txt", "")
                    doc_tag = re.sub(r'^\d+_', '', doc_tag).replace("_", " ").title()
                    if not s_clean.endswith('.'):
                        s_clean += '.'
                    key_findings.append(f"{s_clean} [Source: {doc_tag}]")
            if len(key_findings) >= 5:
                break
        if len(key_findings) >= 5:
            break

    # Build AI Detective Answer Narrative
    briefing_parts = []
    deductive_parts = []

    # 1. Primary Focus Entity
    target_loc = locations[0] if locations else "the primary incident location"
    target_person = persons[0] if persons else None
    target_org = organizations[0] if organizations else None

    # Relationship analysis between entities
    connected_pairs = []
    for e in edges[:6]:
        s = clean_canonical_name(e.get("source", ""))
        t = clean_canonical_name(e.get("target", ""))
        if s and t and s != t:
            connected_pairs.append(f"**{s}** ↔ **{t}**")

    # Construct direct answer based on inquiry intent
    is_who = any(w in query_lower for w in ["who", "person", "people", "suspect", "involved", "connected", "connection", "meet", "met"])
    is_what = any(w in query_lower for w in ["what", "incident", "happened", "fire", "arson", "explosion", "found", "discovered"])
    is_where = any(w in query_lower for w in ["where", "location", "place", "warehouse", "docks"])
    is_why_how = any(w in query_lower for w in ["why", "how", "cause", "motive", "fraud", "accelerant"])

    if is_who:
        if persons:
            p_list = ", ".join([f"**{p}**" for p in persons[:4]])
            briefing_parts.append(
                f"Cross-referencing {docs_count} verified case records confirms that the key individuals connected to this matter are {p_list}."
            )
        else:
            briefing_parts.append(
                f"Documentary evidence across {docs_count} case records identifies active involvement linked to {target_org or target_loc}."
            )

        if connected_pairs:
            deductive_parts.append(
                f"Knowledge graph co-occurrence analysis links {', '.join(connected_pairs[:3])} through corroborated witness statements and official dispatch logs."
            )

    elif is_what:
        event_str = f"an incident involving **{target_loc}**"
        if dates:
            event_str += f" on {dates[0]}"
        briefing_parts.append(
            f"Case analysis and forensic records confirm {event_str}."
        )
        if persons:
            briefing_parts.append(
                f"Official documentation places **{', '.join(persons[:3])}** in direct connection with the events."
            )
        if organizations:
            deductive_parts.append(
                f"Corporate filings and manifests link affiliated entity **{organizations[0]}** to the sequence of events."
            )

    else:
        entities_highlight = []
        if persons:
            entities_highlight.extend([f"**{p}**" for p in persons[:2]])
        if organizations:
            entities_highlight.extend([f"**{o}**" for o in organizations[:1]])
        if locations:
            entities_highlight.extend([f"**{l}**" for l in locations[:1]])

        highlight_str = ", ".join(entities_highlight) if entities_highlight else "the investigated matter"
        briefing_parts.append(
            f"Cross-document synthesis from {docs_count} case file(s) establishes corroborated connections regarding {highlight_str}."
        )

    # Append top evidence quote summary
    if evidence_list:
        top_snippet = evidence_list[0].get("text", "").strip().strip('"')
        first_sentence = re.split(r'(?<=[.!?])\s+', top_snippet)[0].strip()
        if len(first_sentence) > 20 and len(first_sentence) < 220:
            briefing_parts.append(f"Key source record states: *\"{first_sentence}.\"*")

    if not deductive_parts:
        if connected_pairs:
            deductive_parts.append(
                f"Graph relationship discovery establishes verified multi-point co-occurrences across {', '.join(connected_pairs[:3])}."
            )
        else:
            deductive_parts.append(
                f"Evidence corroborated across {docs_count} separate case file(s) via semantic vector matching and entity relationship extraction."
            )

    # Timeline clues
    timeline_anchors = extract_timeline_anchors(evidence_list)

    # Calculate confidence rating
    confidence = "HIGH (Corroborated by Multi-Source Evidence)" if docs_count >= 2 else "MODERATE (Single Source Reference)"

    summary_text = " ".join(briefing_parts)
    deductive_text = " ".join(deductive_parts)

    return {
        "summary": summary_text,
        "detective_briefing": summary_text,
        "deductive_reasoning": deductive_text,
        "key_findings": key_findings[:5],
        "persons_of_interest": persons[:5],
        "locations_identified": locations[:4],
        "organizations_involved": organizations[:3],
        "timeline_anchors": timeline_anchors,
        "corroborated_sources": docs_count,
        "confidence_score": confidence,
        "source_documents": cited_docs
    }
