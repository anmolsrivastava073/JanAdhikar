import json
import logging
from typing import Dict, Any, List
from .classifier import classifier
from .data.jurisdiction_knowledge import resolve_knowledge_graph_node, AUTHORITY_KNOWLEDGE_GRAPH

logger = logging.getLogger(__name__)

class SmartDepartmentResolver:
    def __init__(self):
        self.model = "openai/gpt-oss-120b"

    def _get_client(self):
        return classifier.client

    def resolve(self, route: str, user_problem: str, location: str, extracted_facts: Dict[str, Any], language: str = "English") -> Dict[str, Any]:
        """
        Advanced GraphRAG Resolution Engine:
        1. Queries the hierarchical authority knowledge graph to retrieve domain, CPIO, FAA, address templates, and legal query templates.
        2. If LLM is available, refines the jurisdiction with deep contextual reasoning.
        3. Returns complete authority entity package including verified social media accountability handles.
        """
        # 1. GraphRAG baseline retrieval
        graph_entity = resolve_knowledge_graph_node(user_problem, location or extracted_facts.get("applicant_city", ""))
        
        client = self._get_client()
        if not client:
            return graph_entity

        safe_location = location or extracted_facts.get("applicant_city") or "Local Jurisdiction"
        
        system_prompt = f"""You are an Expert Indian Administrative Law and RTI Jurisdiction Resolver.
Given a citizen's problem, their location, and the retrieved Knowledge Graph node, resolve the EXACT Public Authority,
Central/State Public Information Officer (CPIO/SPIO), First Appellate Authority (FAA), and Official Social Media Handles (@Ministry, @Minister, etc.).

Retrieved Graph Context:
- Domain: {graph_entity.get('domain')}
- Candidate Authority: {graph_entity.get('public_authority_name')}
- Suggested CPIO: {graph_entity.get('pio_designation')}
- Suggested FAA: {graph_entity.get('faa_designation')}
- Candidate Social Handles: {json.dumps(graph_entity.get('social_handles', []))}

Return ONLY a valid JSON matching this schema:
{{
  "public_authority_name": "Exact Department/Authority Name",
  "jurisdiction_level": "Central" | "State" | "Municipal/Local",
  "pio_designation": "The Central Public Information Officer (CPIO) / State PIO, [Specific Branch/Division]",
  "faa_designation": "The First Appellate Authority (FAA), [Designation of Senior Officer]",
  "suggested_address_template": "Official Office Address with [CITY/PIN]",
  "social_handles": ["@MinistryHandle", "@MinisterHandle", "@StateDeptHandle"],
  "reasoning": "1-2 sentence legal explanation why this authority holds the records under Sec 2(h) and Sec 5 of RTI Act"
}}
"""

        user_content = f"Citizen Problem: {user_problem}\nLocation: {safe_location}\nExtracted Facts: {json.dumps(extracted_facts)}"

        try:
            resp = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            parsed = json.loads(resp.choices[0].message.content.strip())
            
            # Merge with statutory query templates from GraphRAG
            parsed["domain"] = graph_entity["domain"]
            parsed["statutory_legal_queries"] = graph_entity["statutory_legal_queries"]
            if not parsed.get("social_handles"):
                parsed["social_handles"] = graph_entity["social_handles"]
            return parsed
        except Exception as e:
            logger.error(f"[Department Resolver] LLM refinement error: {e}")
            return graph_entity

department_resolver = SmartDepartmentResolver()
