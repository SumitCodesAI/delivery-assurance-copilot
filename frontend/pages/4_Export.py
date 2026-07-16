"""
Streamlit page for exporting project data.
"""

import os
import streamlit as st
import httpx

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
        return response.json() if response.status_code == 200 else []
    except:
        return []


def get_export_summary(project_id: str):
    """Get export summary."""
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/v1/projects/{project_id}/export/summary",
            timeout=10
        )
        return response.json() if response.status_code == 200 else None
    except:
        return None


# Add user navbar
from utils.premium_ui import add_user_navbar
add_user_navbar()
st.divider()

# Initialize session state for file downloads
if "csv_data" not in st.session_state:
    st.session_state.csv_data = None
if "json_data" not in st.session_state:
    st.session_state.json_data = None


# Page title
st.title("Export & Reports")
st.markdown("Download your traceability matrix and project data.")

projects = load_projects()
if not projects:
    st.warning("⚠️ No projects found.")
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

        summary = get_export_summary(project_id)

        if summary:
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Requirements", summary.get("total_requirements", 0))
            with col2:
                st.metric("Test Cases", summary.get("total_test_cases", 0))
            with col3:
                st.metric("Criteria", summary.get("total_criteria", 0))
            with col4:
                st.metric("Approval Rate", f"{summary.get('approval_rate', 0):.1f}%")

            st.divider()

            # Coverage metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Covered", summary.get("covered_requirements", 0))
            with col2:
                st.metric("⚠️ Partial", summary.get("partial_requirements", 0))
            with col3:
                st.metric("❌ Gaps", summary.get("gap_requirements", 0))

            st.divider()

            # Export options
            st.subheader("📥 Download Options")

            col1, col2 = st.columns(2)

            with col1:
                if st.button("📊 Download as CSV", use_container_width=True):
                    try:
                        response = httpx.get(
                            f"{BACKEND_URL}/api/v1/projects/{project_id}/export/csv",
                            timeout=30
                        )
                        if response.status_code == 200:
                            st.session_state.csv_data = response.content
                            st.success("✓ CSV generated! Click below to download.")
                        else:
                            st.error(f"Failed to generate CSV: {response.text}")
                    except Exception as e:
                        st.error(f"Error fetching CSV: {str(e)}")
                
                # Show download button if CSV data is available
                if st.session_state.csv_data:
                    st.download_button(
                        label="⬇️ Click to Download CSV",
                        data=st.session_state.csv_data,
                        file_name="traceability_matrix.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

            with col2:
                if st.button("📄 Download as JSON", use_container_width=True):
                    try:
                        response = httpx.get(
                            f"{BACKEND_URL}/api/v1/projects/{project_id}/export/json",
                            timeout=30
                        )
                        if response.status_code == 200:
                            st.session_state.json_data = response.content
                            st.success("✓ JSON generated! Click below to download.")
                        else:
                            st.error(f"Failed to generate JSON: {response.text}")
                    except Exception as e:
                        st.error(f"Error fetching JSON: {str(e)}")
                
                # Show download button if JSON data is available
                if st.session_state.json_data:
                    st.download_button(
                        label="⬇️ Click to Download JSON",
                        data=st.session_state.json_data,
                        file_name="export.json",
                        mime="application/json",
                        use_container_width=True
                    )

            st.divider()

            # Status summary
            st.subheader("📈 Status Summary")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Approved", summary.get("approved_items", 0))
            with col2:
                st.metric("⏳ Pending", summary.get("pending_items", 0))
            with col3:
                st.metric("❌ Rejected", summary.get("rejected_items", 0))

        else:
            st.info("No export data available. Run the pipeline and review items first.")

        st.divider()
        st.markdown("""
        ### 📊 Export Format Details

        **CSV Format** includes:
        - Requirement ID, Title, Priority
        - Test Case Titles
        - Coverage Status (covered/gap/partial)
        - Source Documents
        - Reviewer Status

        **JSON Format** includes:
        - Complete project export
        - All requirements with metadata
        - All test cases and acceptance criteria
        - Full traceability matrix
        - Coverage gaps analysis
        - Summary statistics

        ### 💡 Next Steps

        - Share the CSV with your QA team
        - Import the JSON into your test management tool
        - Use the data for coverage reporting
        - Track test execution against requirements

        """)
