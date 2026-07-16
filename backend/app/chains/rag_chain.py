"""
LangChain RAG chain for retrieving standards and generating test artifacts.
"""

import json
from typing import Literal, List, Optional

from langchain_openai import ChatOpenAI
from langsmith import trace

from app.config import get_settings
from app.models.pydantic_schemas import (
    ExtractedRequirement,
    AcceptanceCriterionOutput,
    TestCaseOutput,
    TestStep,
)
from app.services.chroma_service import ChromaService

settings = get_settings()


class RAGChain:
    """LangChain RAG chain for retrieval-augmented generation."""

    def __init__(self, chroma_service: ChromaService):
        """
        Initialize the RAG chain.

        Args:
            chroma_service: ChromaDB service for retrieval
        """
        self.chroma = chroma_service
        self.llm = ChatOpenAI(
            model="gpt-4o",
            temperature=0,
            api_key=settings.openai_api_key,
            timeout=60,
            max_retries=2,
        )

    @trace(name="rag_retrieve")
    def retrieve_for_requirement(
        self,
        requirement: ExtractedRequirement,
        project_id: str,
    ) -> List[dict]:
        """
        Retrieve relevant chunks from ChromaDB for a requirement.

        Args:
            requirement: Extracted requirement
            project_id: Project UUID for filtering

        Returns:
            List of retrieved chunks with metadata and scores
        """
        # Combine title and description as query
        query_text = f"{requirement.title} {requirement.description}"

        # Query ChromaDB
        chunks = self.chroma.query(
            query_text=query_text,
            project_id=project_id,
            top_k=settings.top_k_retrieval,
        )

        return chunks

    def _format_chunks_for_prompt(self, chunks: List[dict]) -> str:
        """Format retrieved chunks into a readable string for prompts."""
        if not chunks:
            return "[No relevant standards or context retrieved]"

        formatted = []
        for i, chunk in enumerate(chunks, 1):
            score = chunk.get("score", 0)
            text = chunk.get("text", "")
            doc_name = chunk.get("metadata", {}).get("filename", "Unknown")
            formatted.append(f"[{i}] (Score: {score:.2f}, Doc: {doc_name})\n{text[:500]}...")

        return "\n\n".join(formatted)

    @trace(name="rag_generate_criteria")
    def generate_criteria(
        self,
        requirement: ExtractedRequirement,
        retrieved_chunks: List[dict],
    ) -> List[AcceptanceCriterionOutput]:
        """
        Generate acceptance criteria for a requirement using RAG context.

        Args:
            requirement: Extracted requirement
            retrieved_chunks: Retrieved context chunks

        Returns:
            List of acceptance criteria
        """
        formatted_chunks = self._format_chunks_for_prompt(retrieved_chunks)

        system_prompt = """You are a QA Lead reviewing delivery requirements.
Your task is to generate acceptance criteria that are:
- Specific and testable (Given/When/Then format preferred)
- Grounded in the provided standards and context
- Directly mapped to source documents

Always cite the source document and excerpt for each criterion."""

        user_message = f"""REQUIREMENT:
ID: {requirement.req_id}
Title: {requirement.title}
Description: {requirement.description}
Priority: {requirement.priority}

RETRIEVED STANDARDS AND CONTEXT:
{formatted_chunks}

Generate 2-4 acceptance criteria for this requirement.
Each criterion must:
1. Be specific and testable (Given/When/Then format preferred)
2. Cite the source document and excerpt

Return ONLY a valid JSON array where each item has:
- criterion_text: string (the acceptance criterion)
- source_citation: object with doc_name, chunk_id, excerpt (max 200 chars)

No preamble. No markdown. Only JSON."""

        try:
            response = self.llm.invoke(
                [
                    ("system", system_prompt),
                    ("human", user_message),
                ]
            )

            response_text = response.content.strip()
            if response_text.startswith("```"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            criteria_data = json.loads(response_text)
            if not isinstance(criteria_data, list):
                criteria_data = [criteria_data]

            criteria = []
            for crit_data in criteria_data:
                try:
                    # Ensure source_citation is properly structured
                    if "source_citation" in crit_data:
                        if isinstance(crit_data["source_citation"], str):
                            # Try to parse if it's a JSON string
                            try:
                                crit_data["source_citation"] = json.loads(crit_data["source_citation"])
                            except:
                                pass

                    validated = AcceptanceCriterionOutput(**crit_data)
                    criteria.append(validated)
                except Exception as e:
                    print(f"Warning: Failed to validate criterion: {str(e)}")
                    continue

            return criteria if criteria else self._generate_default_criteria(requirement)

        except Exception as e:
            print(f"Error generating criteria: {str(e)}")
            return self._generate_default_criteria(requirement)

    def _generate_default_criteria(
        self,
        requirement: ExtractedRequirement,
    ) -> List[AcceptanceCriterionOutput]:
        """Generate default criteria when LLM fails."""
        return [
            AcceptanceCriterionOutput(
                criterion_text=f"The system shall implement: {requirement.title}",
                source_citation={
                    "doc_name": "direct_extraction",
                    "chunk_id": "direct",
                    "excerpt": requirement.description[:200],
                }
            )
        ]

    @trace(name="rag_generate_tests")
    def generate_test_cases(
        self,
        requirement: ExtractedRequirement,
        criteria: List[AcceptanceCriterionOutput],
        retrieved_chunks: List[dict],
    ) -> List[TestCaseOutput]:
        """
        Generate test cases for a requirement using RAG context.

        Args:
            requirement: Extracted requirement
            criteria: Generated acceptance criteria
            retrieved_chunks: Retrieved context chunks

        Returns:
            List of test cases
        """
        formatted_chunks = self._format_chunks_for_prompt(retrieved_chunks)

        criteria_text = "\n".join([f"- {c.criterion_text}" for c in criteria])

        system_prompt = """You are a Senior QA Engineer.
Your task is to generate comprehensive test cases that:
- Cover the requirement and acceptance criteria
- Are based on industry QA standards and best practices
- Include clear, actionable steps
- Are prioritized appropriately

Each test case must be specific, repeatable, and verifiable."""

        user_message = f"""REQUIREMENT:
ID: {requirement.req_id}
Title: {requirement.title}
Description: {requirement.description}
Priority: {requirement.priority}

ACCEPTANCE CRITERIA:
{criteria_text}

RETRIEVED CONTEXT AND STANDARDS:
{formatted_chunks}

Generate 1-3 test cases for this requirement.
Each test case must have:
- title: descriptive test case title
- preconditions: system state before test execution
- steps: array of objects with step_number (int), action (string), expected_outcome (string)
- expected_result: overall pass condition/final state
- priority: high / medium / low
- requirement_id: the REQ-ID this covers

Return ONLY a valid JSON array of test case objects.
No preamble. No markdown. Only JSON."""

        try:
            response = self.llm.invoke(
                [
                    ("system", system_prompt),
                    ("human", user_message),
                ]
            )

            response_text = response.content.strip()
            if response_text.startswith("```"):
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            tests_data = json.loads(response_text)
            if not isinstance(tests_data, list):
                tests_data = [tests_data]

            test_cases = []
            for test_data in tests_data:
                try:
                    # Ensure requirement_id is set
                    if "requirement_id" not in test_data:
                        test_data["requirement_id"] = requirement.req_id

                    # Parse steps if they're strings
                    if "steps" in test_data and isinstance(test_data["steps"], list):
                        steps = []
                        for i, step in enumerate(test_data["steps"]):
                            if isinstance(step, dict):
                                steps.append(TestStep(**step))
                            elif isinstance(step, str):
                                steps.append(TestStep(
                                    step_number=i + 1,
                                    action=step,
                                    expected_outcome="Step completed successfully"
                                ))
                        test_data["steps"] = steps

                    validated = TestCaseOutput(**test_data)
                    test_cases.append(validated)
                except Exception as e:
                    print(f"Warning: Failed to validate test case: {str(e)}")
                    continue

            return test_cases if test_cases else self._generate_default_test_case(requirement)

        except Exception as e:
            print(f"Error generating test cases: {str(e)}")
            return self._generate_default_test_case(requirement)

    def _generate_default_test_case(
        self,
        requirement: ExtractedRequirement,
    ) -> List[TestCaseOutput]:
        """Generate default test case when LLM fails."""
        return [
            TestCaseOutput(
                title=f"Test: {requirement.title}",
                preconditions="System is in normal operating state",
                steps=[
                    TestStep(
                        step_number=1,
                        action=f"Execute the feature: {requirement.title}",
                        expected_outcome="Feature executes without errors"
                    ),
                    TestStep(
                        step_number=2,
                        action="Verify requirement conditions",
                        expected_outcome="All conditions met: " + requirement.description[:100]
                    ),
                ],
                expected_result=f"Requirement '{requirement.title}' is satisfied",
                priority=requirement.priority,
                requirement_id=requirement.req_id,
            )
        ]
