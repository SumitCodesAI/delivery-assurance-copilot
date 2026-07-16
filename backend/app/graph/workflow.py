"""
LangGraph workflow compilation and execution.
"""

from langgraph.graph import StateGraph, END

from app.graph.state import WorkflowState
from app.graph.nodes import (
    extract_requirements_node,
    retrieve_standards_node,
    generate_criteria_node,
    generate_tests_node,
    analyze_coverage_node,
    assemble_matrix_node,
)


def build_workflow():
    """
    Build and compile the LangGraph requirement processing workflow.

    Returns:
        Compiled StateGraph
    """
    # Create the state graph
    graph = StateGraph(WorkflowState)

    # Add nodes
    graph.add_node("extract", extract_requirements_node)
    graph.add_node("retrieve", retrieve_standards_node)
    graph.add_node("generate_criteria", generate_criteria_node)
    graph.add_node("generate_tests", generate_tests_node)
    graph.add_node("analyze_coverage", analyze_coverage_node)
    graph.add_node("assemble_matrix", assemble_matrix_node)

    # Set entry point
    graph.set_entry_point("extract")

    # Add edges (linear pipeline)
    graph.add_edge("extract", "retrieve")
    graph.add_edge("retrieve", "generate_criteria")
    graph.add_edge("generate_criteria", "generate_tests")
    graph.add_edge("generate_tests", "analyze_coverage")
    graph.add_edge("analyze_coverage", "assemble_matrix")
    graph.add_edge("assemble_matrix", END)

    # Compile the graph
    compiled_graph = graph.compile()

    return compiled_graph


# Create and export the compiled pipeline
pipeline = build_workflow()
