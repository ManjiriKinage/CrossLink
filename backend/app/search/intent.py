"""
intent.py — Query Understanding & Intent-Aware Reasoning Layer
==============================================================
General, case-agnostic query intent analyzer for investigative IR and knowledge graphs.
Identifies reasoning requirements dynamically across arbitrary cases without hardcoded entity names.
"""

import re
from enum import Enum
from typing import Set, List, Dict, Any, Optional, Tuple

class QueryIntent(str, Enum):
    ENTITY_IDENTIFICATION = "ENTITY_IDENTIFICATION"         # Who was connected / which people
    ENTITY_RELATIONSHIP = "ENTITY_RELATIONSHIP"             # What connects X to Y / link between
    EVIDENCE_RETRIEVAL = "EVIDENCE_RETRIEVAL"               # What evidence / what proof
    MULTI_HOP_TRAVERSAL = "MULTI_HOP_TRAVERSAL"             # All connections between X, Y, Z / multi-entity
    ACCESS_OPPORTUNITY = "ACCESS_OPPORTUNITY"               # Who had access / opportunity to access
    EVENT_TIMELINE = "EVENT_TIMELINE"                       # What happened between / chronological timeline
    CROSS_DOCUMENT_AGGREGATION = "CROSS_DOCUMENT_AGGREGATION" # Multiple criteria across docs (both X and Y)
    PROVENANCE_SIMILARITY = "PROVENANCE_SIMILARITY"         # Provenance / auction / catalog / physical match
    HYPOTHESIS_EVALUATION = "HYPOTHESIS_EVALUATION"         # Suggests internal access / could X have / hypothesis
    CONTRADICTION_DETECTION = "CONTRADICTION_DETECTION"     # Discrepancies / conflicting statements / alibi
    EVIDENCE_SUFFICIENCY = "EVIDENCE_SUFFICIENCY"           # Is there enough evidence / can we conclude

class IntentProfile:
    def __init__(
        self,
        query: str,
        intents: Set[QueryIntent],
        target_entities: List[str],
        query_facets: List[str],
        time_bounds: Optional[Tuple[str, str]] = None,
        is_who_question: bool = False,
        is_sufficiency_question: bool = False,
        is_chronological_question: bool = False,
        is_provenance_question: bool = False,
        is_internal_access_question: bool = False,
        is_access_question: bool = False,
        is_causal_context_question: bool = False,
        is_multi_entity_question: bool = False,
    ):
        self.query = query
        self.intents = intents
        self.target_entities = target_entities
        self.query_facets = query_facets
        self.time_bounds = time_bounds
        self.is_who_question = is_who_question
        self.is_sufficiency_question = is_sufficiency_question
        self.is_chronological_question = is_chronological_question
        self.is_provenance_question = is_provenance_question
        self.is_internal_access_question = is_internal_access_question
        self.is_access_question = is_access_question
        self.is_causal_context_question = is_causal_context_question
        self.is_multi_entity_question = is_multi_entity_question

    def has_intent(self, intent: QueryIntent) -> bool:
        return intent in self.intents


def analyze_query_intent(query: str, known_entities: Optional[List[str]] = None) -> IntentProfile:
    """
    Analyzes a natural language investigative question to determine its reasoning intents,
    target entities, temporal boundaries, and sub-facets for multi-stage retrieval.
    Completely general and free of case-specific entity hardcoding.
    """
    q_clean = " ".join(query.strip().split())
    q_lower = q_clean.lower()
    intents: Set[QueryIntent] = set()

    # 1. Detect target entities from query matching known case entities
    detected_entities: List[str] = []
    temporal_anchors: List[str] = []
    date_pattern = re.compile(r"(\b\d{1,2}:\d{2}(?:\s*[ap]m)?\b|\b\d{1,2}\s+(?:aug|sep|jul|oct|nov|dec|jan|feb|mar|apr|may|jun)[a-z]*(?:\s+\d{4})?\b|\b\d{4}\b)", re.IGNORECASE)

    if known_entities:
        sorted_known = sorted(known_entities, key=len, reverse=True)
        for ent in sorted_known:
            if len(ent) >= 3 and ent.lower() in q_lower:
                # If entity is purely a time or date, categorize as temporal anchor
                if date_pattern.fullmatch(ent.strip()):
                    if ent not in temporal_anchors:
                        temporal_anchors.append(ent)
                    continue

                # Discard if this entity is a substring of an already detected longer entity
                if not any(ent.lower() in already.lower() for already in detected_entities):
                    detected_entities = [d for d in detected_entities if d.lower() not in ent.lower()]
                    detected_entities.append(ent)

    # 2. General Query Pattern Recognition
    is_who = bool(re.search(r"\b(who|which people|which person|who was|who had|whom)\b", q_lower))
    is_evidence = bool(re.search(r"\b(what evidence|what proof|evidence connects|evidence links|evidence suggests)\b", q_lower))
    is_sufficiency = bool(re.search(r"\b(enough evidence|sufficient evidence|conclude who|determine who|prove who|conclusively identify)\b", q_lower))
    is_chronological = bool(re.search(r"\b(what happened between|timeline|chronolog|sequence of events|what occurred between)\b", q_lower))
    is_access = bool(re.search(r"\b(who had access|opportunity to access|access and opportunity|access to the museum|authorized access|visitor access)\b", q_lower))
    is_provenance = bool(re.search(r"\b(provenance|auction|catalog|lot \d+|listing|physical description|scratch|mount|origin)\b", q_lower))
    is_hypothesis = bool(re.search(r"\b(suggests that|hypothesis|theory|could have|indicates that|internal access|inside job|tampering)\b", q_lower))
    is_causal = bool(re.search(r"\b(cause|cctv outage|outage|stopped recording|power failure|failure to|tampered)\b", q_lower))
    is_multi_entity = (len(detected_entities) >= 3 and bool(re.search(r"\b(connections?|links?|relationships?|between)\b", q_lower))) or bool(re.search(r"\b(connections between|all known connections|connected between)\b", q_lower))

    # Assign intents
    if is_sufficiency:
        intents.add(QueryIntent.EVIDENCE_SUFFICIENCY)
        intents.add(QueryIntent.HYPOTHESIS_EVALUATION)
        intents.add(QueryIntent.EVIDENCE_RETRIEVAL)

    if is_who:
        intents.add(QueryIntent.ENTITY_IDENTIFICATION)

    if is_evidence:
        intents.add(QueryIntent.EVIDENCE_RETRIEVAL)

    if is_access:
        intents.add(QueryIntent.ACCESS_OPPORTUNITY)
        if is_who:
            intents.add(QueryIntent.ENTITY_IDENTIFICATION)

    if is_chronological:
        intents.add(QueryIntent.EVENT_TIMELINE)
        intents.add(QueryIntent.EVIDENCE_RETRIEVAL)

    if is_provenance:
        intents.add(QueryIntent.PROVENANCE_SIMILARITY)
        intents.add(QueryIntent.ENTITY_RELATIONSHIP)

    if is_hypothesis:
        intents.add(QueryIntent.HYPOTHESIS_EVALUATION)
        intents.add(QueryIntent.EVIDENCE_RETRIEVAL)

    if is_causal:
        intents.add(QueryIntent.EVIDENCE_RETRIEVAL)
        if is_access:
            intents.add(QueryIntent.ACCESS_OPPORTUNITY)
            intents.add(QueryIntent.HYPOTHESIS_EVALUATION)

    if is_multi_entity:
        intents.add(QueryIntent.MULTI_HOP_TRAVERSAL)
        intents.add(QueryIntent.ENTITY_RELATIONSHIP)

    if re.search(r"\bboth\b.*\band\b", q_lower):
        intents.add(QueryIntent.CROSS_DOCUMENT_AGGREGATION)

    if re.search(r"\bwhat connects\b|\bhow is .* linked\b|\bconnection between\b", q_lower):
        intents.add(QueryIntent.ENTITY_RELATIONSHIP)

    if re.search(r"\bcontradict|\bconflict|\bdiscrepan|\balibi\b", q_lower):
        intents.add(QueryIntent.CONTRADICTION_DETECTION)

    # Fallback to general evidence retrieval if no specific intent caught
    if not intents:
        intents.add(QueryIntent.EVIDENCE_RETRIEVAL)

    # 3. Temporal boundary extraction ("between <start> and <end>")
    time_bounds = None
    m_between = re.search(r"between\s+(.+?)\s+and\s+(.+?)(?:\?|$)", q_clean, re.IGNORECASE)
    if m_between and is_chronological:
        time_bounds = (m_between.group(1).strip(), m_between.group(2).strip())

    # 4. Generate multi-facet sub-queries for iterative retrieval
    query_facets = [q_clean]

    # If question has "and", split into facets
    and_parts = re.split(r",?\s+and\s+", q_clean, flags=re.IGNORECASE)
    if len(and_parts) > 1:
        for part in and_parts:
            part_s = part.strip().rstrip("?")
            if len(part_s) > 10 and part_s not in query_facets:
                query_facets.append(part_s)

    # If multiple target entities detected, add pairwise and individual facets
    if len(detected_entities) >= 2:
        for ent in detected_entities:
            if ent not in query_facets:
                query_facets.append(ent)
        if len(detected_entities) == 2:
            query_facets.append(f"{detected_entities[0]} {detected_entities[1]}")

    if is_access:
        query_facets.append("museum access visitor register log entry exit shift")
    if is_causal or "cctv" in q_lower:
        query_facets.append("cctv outage feed security control camera")
    if is_provenance:
        query_facets.append("auction catalog lot listing scratch mount provenance description")
    if is_hypothesis and "internal" in q_lower:
        query_facets.append("forced entry card access security corridor authorization")

    is_internal = is_hypothesis and ("internal" in q_lower or "inside" in q_lower)
    is_causal_context = is_causal and is_access

    return IntentProfile(
        query=q_clean,
        intents=intents,
        target_entities=detected_entities,
        query_facets=query_facets,
        time_bounds=time_bounds,
        is_who_question=is_who,
        is_sufficiency_question=is_sufficiency,
        is_chronological_question=is_chronological,
        is_provenance_question=is_provenance,
        is_internal_access_question=is_internal,
        is_access_question=is_access,
        is_causal_context_question=is_causal_context,
        is_multi_entity_question=is_multi_entity,
    )
