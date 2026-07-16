"""
Streamlit page for viewing extracted requirements and running the pipeline.
"""

import os
import streamlit as st
import httpx
from datetime import datetime

from utils.premium_ui import set_premium_theme

set_premium_theme()

# Check authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("🔐 Please log in first")
    st.switch_page("pages/0_Login.py")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def load_projects():
    """Load list of projects."""
    try:
        response = httpx.get(f"{BACKEND_URL}/api/v1/projects", timeout=10)
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error loading projects: {str(e)}")
        return []


def run_pipeline(project_id: str):
    """Run the extraction pipeline."""
    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/v1/projects/{project_id}/run-pipeline",
            json={},
            timeout=180  # 3 minute timeout for long-running pipeline
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Pipeline error: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error running pipeline: {str(e)}")
        return None


def load_requirements(project_id: str, skip: int = 0, limit: int = 100):
    """Load requirements for a project."""
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/v1/projects/{project_id}/requirements",
            params={"skip": skip, "limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error loading requirements: {str(e)}")
        return []


# Add user navbar
from utils.premium_ui import add_user_navbar
add_user_navbar()
st.divider()

# Page title
st.title("Requirements")
st.markdown("Extract requirements from your uploaded documents using AI.")

# Initialize session state
if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False

# Project selection
projects = load_projects()
if not projects:
    st.warning("⚠️ No projects found. Please create a project and upload documents first.")
else:
    project_names = [p["name"] for p in projects]
    selected_project_name = st.selectbox("Select project:", options=project_names)

    selected_project = next(
        (p for p in projects if p["name"] == selected_project_name),
        None
    )

    if selected_project:
        project_id = selected_project["id"]

        st.divider()
        st.subheader(f"📁 {selected_project['name']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Documents", selected_project.get("document_count", 0))
        with col2:
            st.metric("Status", selected_project.get("status", "unknown"))
        with col3:
            st.metric("Created", selected_project.get("created_at", "").split("T")[0])

        st.divider()

        # Pipeline execution section
        st.subheader("🚀 Run AI Pipeline")
        st.write("""
        Click below to run the AI pipeline which will:
        1. Extract requirements from documents
        2. Retrieve relevant QA standards from knowledge base
        3. Generate acceptance criteria
        4. Generate test cases
        5. Analyze coverage gaps
        6. Build traceability matrix
        """)

        col1, col2 = st.columns([2, 1])
        with col1:
            if st.button("▶️ Run Pipeline", key="run_pipeline_btn", use_container_width=True):
                st.session_state.pipeline_running = True

        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        # Pipeline execution
        if st.session_state.pipeline_running:
            progress_placeholder = st.empty()
            status_placeholder = st.empty()

            with progress_placeholder.container():
                progress_bar = st.progress(0)
                status = st.empty()

                # Run pipeline
                status.write("⏳ Starting pipeline...")
                progress_bar.progress(20)

                status.write("📖 Extracting requirements from documents...")
                progress_bar.progress(40)

                status.write("🔍 Retrieving QA standards from knowledge base...")
                progress_bar.progress(60)

                status.write("✍️ Generating acceptance criteria...")
                progress_bar.progress(70)

                status.write("🧪 Generating test cases...")
                progress_bar.progress(80)

                status.write("📊 Building traceability matrix...")
                progress_bar.progress(90)

                # Actually run the pipeline
                result = run_pipeline(project_id)

                if result:
                    progress_bar.progress(100)
                    status.success("✅ Pipeline completed!")

                    st.divider()
                    st.subheader("📊 Pipeline Results")

                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Requirements", result.get("requirements_count", 0))
                    with col2:
                        st.metric("Test Cases", result.get("test_cases_count", 0))
                    with col3:
                        st.metric("Coverage Gaps", result.get("coverage_gaps_count", 0))
                    with col4:
                        st.metric("Status", result.get("status", "unknown"))

                    if result.get("errors"):
                        with st.expander("⚠️ Errors During Processing"):
                            for error in result["errors"]:
                                st.warning(error)

                    st.info("👉 Next: Go to the **Review** page to approve/edit the generated items!")

                else:
                    status.error("❌ Pipeline failed!")

            st.session_state.pipeline_running = False

        st.divider()

        # Requirements list section
        st.subheader("📋 Extracted Requirements")

        requirements = load_requirements(project_id)

        if requirements:
            st.write(f"Showing {len(requirements)} requirements")

            for req in requirements:
                # Color-coded priority badge
                if req["priority"] == "high":
                    priority_color = "🔴"
                elif req["priority"] == "medium":
                    priority_color = "🟡"
                else:
                    priority_color = "🟢"

                # Ambiguity warning
                ambiguity_mark = "⚠️" if req["ambiguity_flag"] else "✅"

                # Create expander for each requirement
                with st.expander(
                    f"{req['req_id']}: {req['title']} {priority_color} {ambiguity_mark}",
                    expanded=False
                ):
                    col1, col2 = st.columns([1, 1])

                    with col1:
                        st.write(f"**Priority**: {req['priority'].upper()}")
                        st.write(f"**Ambiguity Flag**: {req['ambiguity_flag']}")

                    with col2:
                        if req["ambiguity_flag"]:
                            st.warning(f"**Ambiguity Notes**: {req.get('ambiguity_notes', 'N/A')}")

                    st.write("**Description**:")
                    st.write(req["description"])

        else:
            st.info("No requirements extracted yet. Run the pipeline above to generate requirements.")

        st.divider()

        # Statistics
        st.subheader("📊 Requirement Statistics")

        if requirements:
            # Count by priority
            priority_counts = {}
            for req in requirements:
                p = req.get("priority", "medium")
                priority_counts[p] = priority_counts.get(p, 0) + 1

            # Count ambiguous
            ambiguous_count = sum(1 for req in requirements if req.get("ambiguity_flag", False))

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("High Priority", priority_counts.get("high", 0))
            with col2:
                st.metric("Medium Priority", priority_counts.get("medium", 0))
            with col3:
                st.metric("Low Priority", priority_counts.get("low", 0))

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Ambiguous", ambiguous_count)
            with col2:
                st.metric("Clear", len(requirements) - ambiguous_count)

        st.divider()
        st.markdown("""
        ### 📝 What Happens Next

        1. **Requirements Extracted**: AI analyzes documents and extracts structured requirements
        2. **Context Retrieved**: RAG system retrieves relevant QA standards and policies
        3. **Criteria Generated**: AI creates acceptance criteria based on standards
        4. **Tests Generated**: AI creates detailed test cases with steps
        5. **Coverage Analyzed**: System identifies test coverage gaps
        6. **Review Ready**: Go to the **Review** page to approve/edit items

        ### 🚨 Handling Ambiguous Requirements

        Requirements marked with ⚠️ have ambiguous language. These may need refinement:
        - Check the ambiguity notes for specific issues
        - Edit criteria and tests in the Review page if needed
        - Coverage will be marked "partial" for ambiguous requirements

        Ready to review? Head to the **Review** page! 👉
        """)
