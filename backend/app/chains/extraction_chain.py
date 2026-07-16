"""
LangChain chain for requirement extraction from documents.
"""

import json
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langsmith import trace

from app.config import get_settings
from app.models.pydantic_schemas import ExtractedRequirement, ExtractionResult

settings = get_settings()


class ExtractionChain:
    """LangChain chain for extracting requirements from documents."""

    def __init__(self):
        """Initialize the extraction chain."""
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=settings.openai_api_key,
            timeout=60,
            max_retries=2,
        )

        self.parser = JsonOutputParser(pydantic_object=ExtractedRequirement)

        # System prompt for requirement extraction
        self.system_prompt = """You are an expert Business Analyst and QA Engineer.
Your task is to extract ALL requirements from the provided document.

For each requirement, output:
- req_id: sequential string like REQ-001, REQ-002, etc.
- title: short descriptive title (maximum 10 words)
- description: full requirement description (be comprehensive)
- priority: high / medium / low based on business criticality language in the document
- ambiguity_flag: true if the requirement uses vague language (words like "should", "might", "TBD", "unclear", "assumed", "approximately", etc.)
- ambiguity_notes: explain why it is ambiguous if ambiguity_flag is true, otherwise null
- source_chunk_ids: list of identifiers where this requirement appears (use the format provided in context, or "direct_extraction")

Return ONLY a valid JSON array of requirement objects. Do not include any preamble, markdown, explanation, or other text.
Each object must be valid JSON that can be parsed.
"""

    @trace(name="extraction_chain")
    def run(
        self,
        document_text: str,
        doc_type: str,
        doc_name: str,
        doc_id: str,
    ) -> ExtractionResult:
        """
        Extract requirements from document text.

        Args:
            document_text: Full text of the document
            doc_type: Type of document (brd, user_story, api_spec, nfr, qa_policy, etc.)
            doc_name: Filename of the document
            doc_id: UUID of the document

        Returns:
            ExtractionResult with list of ExtractedRequirement objects

        Raises:
            ValueError: If LLM response cannot be parsed
        """
        # Build prompt
        user_message = f"""DOCUMENT TYPE: {doc_type}
DOCUMENT NAME: {doc_name}

DOCUMENT CONTENT:
{document_text}

Extract all requirements from this document and return them as a JSON array."""

        messages = [
            ("system", self.system_prompt),
            ("human", user_message),
        ]

        prompt = ChatPromptTemplate.from_messages(messages)

        # Create chain
        chain = prompt | self.llm

        # Invoke chain
        response = chain.invoke({})

        # Parse response
        try:
            # Extract JSON from response
            response_text = response.content.strip()

            # Try to parse as JSON
            if response_text.startswith("```"):
                # Remove markdown code blocks if present
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            requirements_data = json.loads(response_text)

            # Ensure it's a list
            if not isinstance(requirements_data, list):
                requirements_data = [requirements_data]

            # Validate and convert to ExtractedRequirement objects
            requirements = []
            for i, req_data in enumerate(requirements_data):
                try:
                    # Ensure req_id is present
                    if "req_id" not in req_data:
                        req_data["req_id"] = f"REQ-{i+1:03d}"

                    # Validate against Pydantic schema
                    validated_req = ExtractedRequirement(**req_data)
                    requirements.append(validated_req)
                except Exception as e:
                    # Log but continue
                    print(f"Warning: Failed to validate requirement {i}: {str(e)}")
                    continue

            if not requirements:
                raise ValueError("No valid requirements could be extracted from LLM response")

            return ExtractionResult(
                document_id=doc_id,
                requirements=requirements,
            )

        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse LLM response as JSON: {str(e)}\nResponse: {response_text}")
        except Exception as e:
            raise ValueError(f"Error in extraction chain: {str(e)}")
