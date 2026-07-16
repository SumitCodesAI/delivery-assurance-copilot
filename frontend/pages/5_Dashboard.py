"""
Streamlit page for project dashboard and metrics.
"""

import os
import streamlit as st
import httpx
import plotly.express as px
import pandas as pd

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

# Page title
st.title("Dashboard")
st.markdown("View project metrics and analytics.")

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
            # Key metrics
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Requirements", summary.get("total_requirements", 0))
            with col2:
                st.metric("Test Cases", summary.get("total_test_cases", 0))
            with col3:
                st.metric("Approval Rate", f"{summary.get('approval_rate', 0):.1f}%")
            with col4:
                st.metric("Covered", summary.get("covered_requirements", 0))
            with col5:
                st.metric("Gaps", summary.get("gap_requirements", 0))

            st.divider()

            # Charts
            col1, col2 = st.columns(2)

            with col1:
                # Coverage distribution
                coverage_data = {
                    "Status": ["Covered", "Partial", "Gap"],
                    "Count": [
                        summary.get("covered_requirements", 0),
                        summary.get("partial_requirements", 0),
                        summary.get("gap_requirements", 0),
                    ]
                }
                coverage_df = pd.DataFrame(coverage_data)
                fig = px.pie(
                    coverage_df,
                    values="Count",
                    names="Status",
                    title="Coverage Distribution",
                    color_discrete_map={"Covered": "#00CC96", "Partial": "#FFD700", "Gap": "#EF553B"}
                )
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                # Approval status
                status_data = {
                    "Status": ["Approved", "Pending", "Rejected"],
                    "Count": [
                        summary.get("approved_items", 0),
                        summary.get("pending_items", 0),
                        summary.get("rejected_items", 0),
                    ]
                }
                status_df = pd.DataFrame(status_data)
                fig = px.bar(
                    status_df,
                    x="Status",
                    y="Count",
                    title="Review Status",
                    color="Status",
                    color_discrete_map={"Approved": "#00CC96", "Pending": "#FFD700", "Rejected": "#EF553B"}
                )
                st.plotly_chart(fig, use_container_width=True)

            st.divider()

            # Detailed metrics
            st.subheader("📈 Detailed Metrics")

            metric_col1, metric_col2, metric_col3 = st.columns(3)

            with metric_col1:
                st.info(f"**Requirements**: {summary.get('total_requirements', 0)}")
                st.caption(f"Avg {summary.get('total_test_cases', 0) // max(1, summary.get('total_requirements', 1)):.1f} tests per req")

            with metric_col2:
                st.success(f"**Approved Items**: {summary.get('approved_items', 0)}")
                total_items = (summary.get('approved_items', 0) +
                               summary.get('pending_items', 0) +
                               summary.get('rejected_items', 0))
                if total_items > 0:
                    st.caption(f"Approval Rate: {summary.get('approval_rate', 0):.1f}%")

            with metric_col3:
                gap_count = summary.get('gap_requirements', 0)
                if gap_count > 0:
                    st.warning(f"**Coverage Gaps**: {gap_count}")
                    st.caption(f"{gap_count / max(1, summary.get('total_requirements', 1)) * 100:.1f}% of requirements")
                else:
                    st.success("**Coverage Gaps**: 0 ✅")

            st.divider()

            # Project info
            st.subheader("📋 Project Information")

            info_col1, info_col2 = st.columns(2)

            with info_col1:
                st.write(f"**Name**: {selected_project.get('name', 'N/A')}")
                st.write(f"**Status**: {selected_project.get('status', 'N/A').upper()}")
                st.write(f"**Created**: {selected_project.get('created_at', 'N/A').split('T')[0]}")

            with info_col2:
                st.write(f"**Documents**: {selected_project.get('document_count', 0)}")
                if selected_project.get('description'):
                    st.write(f"**Description**: {selected_project.get('description')}")

        else:
            st.info("No data available. Run the pipeline first.")

        st.divider()
        st.markdown("""
        ### 📊 Dashboard Overview

        This dashboard provides:
        - **Coverage Distribution**: Pie chart showing covered/partial/gap breakdown
        - **Review Status**: Bar chart showing approved/pending/rejected items
        - **Key Metrics**: At-a-glance project statistics
        - **Project Info**: Metadata and timeline information

        ### 🎯 What These Metrics Mean

        - **Covered**: Requirements with adequate test coverage
        - **Partial**: Requirements with ambiguity or incomplete coverage
        - **Gap**: Requirements without test coverage
        - **Approval Rate**: Percentage of items approved vs total

        ### 💡 How to Improve Metrics

        1. Review ambiguous requirements in the **Review** page
        2. Add tests for any gaps using the edit feature
        3. Approve refined items to increase approval rate
        4. Use exports to track progress over time
        """)
