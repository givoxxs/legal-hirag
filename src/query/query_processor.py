import time
from typing import Dict, List, Any, Optional
from ..models.query_models import LegalQueryParam, LegalQueryResult, LegalQueryMode
from ..storage.storage_manager import LegalStorageManager
from .context_builder import LegalContextBuilder
from ..utils.config import load_config
from litellm import completion


class LegalQueryProcessor:
    """Main query processor for legal HiRAG system"""

    def __init__(
        self, storage_manager: LegalStorageManager, llm_config: Dict[str, Any]
    ):
        self.storage = storage_manager
        self.context_builder = LegalContextBuilder(storage_manager)
        self.llm_config = llm_config

        # Load prompts
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict[str, Any]:
        """Load query prompts from configuration"""
        import yaml
        from pathlib import Path

        prompts = {}
        prompts_dir = Path("src/config/prompts")

        # Load query templates
        query_templates_file = prompts_dir / "query_templates.yaml"
        if query_templates_file.exists():
            with open(query_templates_file, "r", encoding="utf-8") as f:
                query_data = yaml.safe_load(f)
                prompts.update(query_data.get("query_templates", {}))

        return prompts

    async def process_query(
        self, query: str, params: LegalQueryParam
    ) -> LegalQueryResult:
        """Process a legal query and return structured result"""

        start_time = time.time()

        try:
            # Build context based on query mode
            context = await self._build_query_context(query, params)

            # Generate response using LLM
            response = await self._generate_response(query, context, params)

            # Extract metadata from context
            entities_retrieved = context.get("entities", [])
            provisions_referenced = context.get("provisions", [])
            cross_references = context.get("cross_references", [])

            processing_time = time.time() - start_time

            return LegalQueryResult(
                query=query,
                answer=response,
                mode=params.mode,
                context_used=context,
                entities_retrieved=entities_retrieved,
                provisions_referenced=provisions_referenced,
                cross_references=cross_references,
                processing_time=processing_time,
                sources=self._extract_sources(context),
            )

        except Exception as e:
            print(f"Error processing query: {e}")
            return LegalQueryResult(
                query=query,
                answer=self.prompts.get(
                    "fail_response", "Đã xảy ra lỗi khi xử lý câu hỏi."
                ),
                mode=params.mode,
                context_used={},
                processing_time=time.time() - start_time,
            )

    async def _build_query_context(
        self, query: str, params: LegalQueryParam
    ) -> Dict[str, Any]:
        """Build context based on query mode"""

        if params.mode == LegalQueryMode.LOCAL:
            return await self.context_builder.build_local_context(query, params)
        elif params.mode == LegalQueryMode.GLOBAL:
            return await self.context_builder.build_global_context(query, params)
        elif params.mode == LegalQueryMode.BRIDGE:
            return await self.context_builder.build_bridge_context(query, params)
        elif params.mode == LegalQueryMode.HIERARCHICAL:
            return await self.context_builder.build_hierarchical_context(query, params)
        elif params.mode == LegalQueryMode.PROVISION:
            return await self.context_builder.build_provision_context(query, params)
        else:
            # Default to hierarchical
            return await self.context_builder.build_hierarchical_context(query, params)

    async def _generate_response(
        self, query: str, context: Dict[str, Any], params: LegalQueryParam
    ) -> str:
        """Generate response using LLM"""

        # Select appropriate prompt template
        prompt_key = self._get_prompt_key(params.mode)
        system_prompt_template = self.prompts.get(
            prompt_key, self.prompts.get("local_rag_response", "")
        )

        # Format context for LLM
        formatted_context = self._format_context_for_llm(context)

        # Create system prompt
        system_prompt = system_prompt_template.format(
            context_data=formatted_context, response_type=params.response_type
        )

        # Call LLM (implement based on your chosen LLM)
        response = await self._call_llm(query, system_prompt)

        return response

    def _get_prompt_key(self, mode: LegalQueryMode) -> str:
        """Get appropriate prompt key for query mode"""
        mode_to_prompt = {
            LegalQueryMode.LOCAL: "local_rag_response",
            LegalQueryMode.GLOBAL: "global_response",
            LegalQueryMode.BRIDGE: "bridge_response",
            LegalQueryMode.HIERARCHICAL: "hierarchical_response",
            LegalQueryMode.PROVISION: "local_rag_response",
        }
        return mode_to_prompt.get(mode, "local_rag_response")

    def _format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """Format context data for LLM consumption"""
        formatted_parts = []

        # Format entities
        if "entities" in context and context["entities"]:
            entities_text = "THỰC THỂ PHÁP LÝ:\n"
            for i, entity in enumerate(context["entities"]):
                entities_text += f"{i+1}. {entity.get('name', '')}: {entity.get('description', '')}\n"
            formatted_parts.append(entities_text)

        # Format provisions
        if "provisions" in context and context["provisions"]:
            provisions_text = "ĐIỀU KHOẢN PHÁP LUẬT:\n"
            for i, provision in enumerate(context["provisions"]):
                provisions_text += f"{i+1}. {provision.get('title', '')}\n{provision.get('content', '')}\n\n"
            formatted_parts.append(provisions_text)

        # Format relationships
        if "relationships" in context and context["relationships"]:
            relations_text = "MỐI QUAN HỆ:\n"
            for i, rel in enumerate(context["relationships"]):
                relations_text += f"{i+1}. {rel.get('source', '')} → {rel.get('target', '')}: {rel.get('description', '')}\n"
            formatted_parts.append(relations_text)

        return "\n\n".join(formatted_parts)

    async def _call_llm(self, query: str, system_prompt: str) -> str:
        """Call LLM API - implement based on your chosen LLM"""
        try:
            response = completion(
                model="gemini/gemini-2.0-flash",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                api_key=self.llm_config.get("gemini").get("api_key"),
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Lỗi LiteLLM: {str(e)}"

    def _extract_sources(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Extract source information from context"""
        sources = []

        if "provisions" in context:
            for provision in context["provisions"]:
                sources.append(
                    {
                        "type": "provision",
                        "id": provision.get("id", ""),
                        "title": provision.get("title", ""),
                        "level": provision.get("level", ""),
                    }
                )

        return sources
