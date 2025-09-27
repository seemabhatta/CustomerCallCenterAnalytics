"""
Graph Query Service - Agentic natural language to knowledge graph queries.

Core Principles:
- NO FALLBACK LOGIC - fail fast if LLM can't interpret
- Completely agentic - LLM makes all decisions
- Prompts in separate files, reuse LLM client v2
"""
from typing import Dict, Any
import logging
import os

logger = logging.getLogger(__name__)


class GraphQueryService:
    """Agentic service for natural language knowledge graph queries."""

    def __init__(self):
        from ..infrastructure.graph.unified_graph_manager import get_unified_graph_manager
        from ..infrastructure.llm.llm_client_v2 import LLMClientV2
        self.graph = get_unified_graph_manager()
        self.llm = LLMClientV2()
        self.prompts_dir = "prompts"

    async def ask(self, question: str) -> Dict[str, Any]:
        """Ask a natural language question about the knowledge graph."""
        if not question or not question.strip():
            raise ValueError("Question cannot be empty")

        try:
            # Load prompts from files
            query_prompt = self._load_prompt("graph_query_agent.txt", {"question": question})

            # Let LLM generate Cypher query
            from ..infrastructure.llm.llm_client_v2 import RequestOptions
            response = await self.llm.arun(
                messages=[{"role": "user", "content": query_prompt}],
                options=RequestOptions(temperature=0.1, max_output_tokens=800)
            )

            # Extract and execute query
            cypher_query = self._extract_cypher(response.text)
            if not cypher_query:
                raise RuntimeError("LLM failed to generate valid Cypher query")

            raw_results = await self._execute_cypher(cypher_query)

            # Let LLM explain results
            explanation = await self._explain_results(question, cypher_query, raw_results)

            return {
                "question": question,
                "cypher_query": cypher_query,
                "results": raw_results,
                "explanation": explanation,
                "count": len(raw_results)
            }

        except Exception as e:
            logger.error(f"Graph query failed for question '{question}': {e}")
            raise RuntimeError(f"Failed to process question: {str(e)}")

    def _load_prompt(self, filename: str, variables: Dict[str, str] = None) -> str:
        """Load prompt from file and substitute variables."""
        prompt_path = os.path.join(self.prompts_dir, filename)

        if not os.path.exists(prompt_path):
            raise RuntimeError(f"Prompt file not found: {prompt_path}")

        with open(prompt_path, 'r') as f:
            prompt = f.read()

        if variables:
            for key, value in variables.items():
                prompt = prompt.replace(f"{{{key}}}", str(value))

        return prompt

    def _extract_cypher(self, llm_response: str) -> str:
        """Extract Cypher query from LLM response."""
        lines = llm_response.split('\n')
        in_cypher_block = False
        cypher_lines = []

        for line in lines:
            if line.strip().startswith('```cypher'):
                in_cypher_block = True
                continue
            elif line.strip().startswith('```') and in_cypher_block:
                break
            elif in_cypher_block:
                cypher_lines.append(line)

        cypher_query = '\n'.join(cypher_lines).strip()

        if not cypher_query or not any(keyword in cypher_query.upper() for keyword in ['MATCH', 'RETURN']):
            return None

        return cypher_query

    async def _execute_cypher(self, cypher_query: str) -> list:
        """Execute Cypher query against knowledge graph."""
        # Safety check - NO FALLBACK
        query_upper = cypher_query.upper()
        forbidden_keywords = ['CREATE', 'DELETE', 'SET', 'REMOVE', 'MERGE', 'DROP']
        if any(keyword in query_upper for keyword in forbidden_keywords):
            raise RuntimeError(f"Query contains forbidden operations")

        result = await self.graph._execute_async(cypher_query)

        results = []
        while result.has_next():
            row = result.get_next()
            row_data = []
            for item in row:
                if hasattr(item, '__dict__'):
                    row_data.append(dict(item))
                else:
                    row_data.append(item)
            results.append(row_data)

        return results

    async def _explain_results(self, question: str, cypher_query: str, results: list) -> str:
        """Let LLM explain query results."""
        result_summary = f"Query returned {len(results)} results"
        if results and len(results) <= 5:
            result_summary += f": {results}"
        elif results:
            result_summary += f". Sample: {results[:2]}"

        explain_prompt = self._load_prompt("graph_results_explainer.txt", {
            "question": question,
            "cypher_query": cypher_query,
            "result_summary": result_summary
        })

        from ..infrastructure.llm.llm_client_v2 import RequestOptions
        response = await self.llm.arun(
            messages=[{"role": "user", "content": explain_prompt}],
            options=RequestOptions(temperature=0.3, max_output_tokens=300)
        )
        explanation = response.text

        return explanation.strip()


# Global service instance
_graph_query_service = None

def get_graph_query_service() -> GraphQueryService:
    """Get graph query service instance."""
    global _graph_query_service
    if _graph_query_service is None:
        try:
            _graph_query_service = GraphQueryService()
        except Exception as e:
            logger.error(f"Failed to initialize GraphQueryService: {e}")
            raise RuntimeError(f"Cannot proceed without graph query service: {e}")
    return _graph_query_service