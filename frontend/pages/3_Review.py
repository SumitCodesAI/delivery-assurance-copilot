"""
Streamlit page for reviewing and approving generated artifacts.
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
        if response.status_code == 200:
            return response.json()
        return []
    except Exception:
        return []


def get_review_data(project_id: str):
    """Get review data for project."""
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/v1/projects/{project_id}/review",
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception:
        return None


def update_test_case_review(test_case_id: str, status: str, note: str = "", edited_text: str = ""):
    """Update test case review status."""
    try:
        response = httpx.put(
            f"{BACKEND_URL}/api/v1/test-cases/{test_case_id}/review",
            json={
                "reviewer_status": status,
                "reviewer_note": note,
                "edited_text": edited_text if status == "edited" else None,
            },
            timeout=10
        )
        if response.status_code == 200:
            return True, None
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)


def update_criterion_review(criterion_id: str, status: str, note: str = "", edited_text: str = ""):
    """Update criterion review status."""
    try:
        response = httpx.put(
            f"{BACKEND_URL}/api/v1/criteria/{criterion_id}/review",
            json={
                "reviewer_status": status,
                "reviewer_note": note,
                "edited_text": edited_text if status == "edited" else None,
            },
            timeout=10
        )
        if response.status_code == 200:
            return True, None
        else:
            return False, response.text
    except Exception as e:
        return False, str(e)


# Page title
st.title("Review & Approval")
st.markdown("Review generated test cases and acceptance criteria. Approve, reject, or edit items.")

# Add user navbar
from utils.premium_ui import add_user_navbar
add_user_navbar()
st.divider()

# Initialize session state for tracking edits
if "review_changes" not in st.session_state:
    st.session_state.review_changes = {}

# Project selection
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

        # Load review data
        review_data = get_review_data(project_id)

        if review_data and review_data.get("data"):
            data = review_data["data"]

            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)

            approved = 0
            rejected = 0
            pending = 0

            for item in data:
                for crit in item.get("acceptance_criteria", []):
                    if crit["status"] == "approved":
                        approved += 1
                    elif crit["status"] == "rejected":
                        rejected += 1
                    else:
                        pending += 1

                for tc in item.get("test_cases", []):
                    if tc["status"] == "approved":
                        approved += 1
                    elif tc["status"] == "rejected":
                        rejected += 1
                    else:
                        pending += 1

            with col1:
                st.metric("✅ Approved", approved)
            with col2:
                st.metric("⏳ Pending", pending)
            with col3:
                st.metric("❌ Rejected", rejected)
            with col4:
                approval_rate = (approved / (approved + rejected + pending) * 100) if (approved + rejected + pending) > 0 else 0
                st.metric("Approval Rate", f"{approval_rate:.1f}%")

            st.divider()

            # Review items by requirement
            st.subheader("📋 Review Items by Requirement")

            for idx, item in enumerate(data):
                req = item["requirement"]
                criteria = item["acceptance_criteria"]
                test_cases = item["test_cases"]

                # Ambiguity warning
                ambiguity_mark = "⚠️" if req["ambiguity_flag"] else "✅"

                # Use container instead of expander (no nesting allowed in Streamlit)
                with st.container(border=True):
                    st.markdown(f"### {req['req_id']}: {req['title']} {ambiguity_mark}")
                    
                    # Requirement details
                    st.write(f"**Priority**: {req['priority'].upper()}")
                    st.write(f"**Description**: {req['description']}")

                    if req["ambiguity_flag"]:
                        st.warning(f"⚠️ Ambiguous: {req.get('ambiguity_notes', 'N/A')}")

                    st.markdown("---")

                    # Acceptance Criteria Section
                    st.subheader("✅ Acceptance Criteria")

                    if criteria:
                        for crit_idx, crit in enumerate(criteria):
                            crit_key = f"crit_{req['id']}_{crit_idx}"

                            # Use container instead of nested expander
                            with st.container(border=True):
                                st.markdown(f"**Criterion {crit_idx + 1}**: {crit['text'][:80]}... | **Status**: {crit['status'].upper()}")
                                st.write(crit["text"])

                                if crit["source"]:
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.caption(f"📄 {crit['source'].get('doc_name', 'Unknown')}")
                                    with col2:
                                        st.caption(f"🔗 {crit['source'].get('chunk_id', '')}")
                                    with col3:
                                        st.caption(f"📝 {crit['source'].get('excerpt', '')[:50]}...")

                                st.markdown("---")

                                # Review action buttons
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    if st.button("✅ Approve", key=f"{crit_key}_approve"):
                                        success, error = update_criterion_review(crit["id"], "approved")
                                        if success:
                                            st.success("✅ Approved!")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to approve: {error}")

                                with col2:
                                    if st.button("❌ Reject", key=f"{crit_key}_reject"):
                                        st.session_state.review_changes[f"{crit_key}_rejecting"] = True

                                with col3:
                                    if st.button("✏️ Edit", key=f"{crit_key}_edit"):
                                        st.session_state.review_changes[f"{crit_key}_editing"] = True

                                # Reject workflow
                                if st.session_state.review_changes.get(f"{crit_key}_rejecting"):
                                    reject_reason = st.text_area(
                                        "Rejection reason:",
                                        key=f"{crit_key}_reason"
                                    )
                                    if st.button("Confirm Rejection", key=f"{crit_key}_confirm_reject"):
                                        success, error = update_criterion_review(crit["id"], "rejected", reject_reason)
                                        if success:
                                            st.success("❌ Rejected!")
                                            st.session_state.review_changes[f"{crit_key}_rejecting"] = False
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to reject: {error}")

                                # Edit workflow
                                if st.session_state.review_changes.get(f"{crit_key}_editing"):
                                    edited_text = st.text_area(
                                        "Edit criterion text:",
                                        value=crit["text"],
                                        key=f"{crit_key}_edit_text"
                                    )
                                    edit_note = st.text_input(
                                        "Edit notes:",
                                        key=f"{crit_key}_edit_note"
                                    )
                                    if st.button("Save Changes", key=f"{crit_key}_confirm_edit"):
                                        success, error = update_criterion_review(crit["id"], "edited", edit_note, edited_text)
                                        if success:
                                            st.success("✏️ Updated!")
                                            st.session_state.review_changes[f"{crit_key}_editing"] = False
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to save: {error}")

                    else:
                        st.info("No acceptance criteria generated for this requirement.")

                    st.markdown("---")

                    # Test Cases Section
                    st.subheader("🧪 Test Cases")

                    if test_cases:
                        for tc_idx, tc in enumerate(test_cases):
                            tc_key = f"tc_{req['id']}_{tc_idx}"

                            # Use container instead of nested expander
                            with st.container(border=True):
                                st.markdown(f"**Test {tc_idx + 1}**: {tc['title']} | **Status**: {tc['status'].upper()}")
                                
                                # Test case details
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.caption(f"Priority: {tc['priority'].upper()}")
                                with col2:
                                    st.caption(f"Steps: {len(tc['steps']) if isinstance(tc['steps'], list) else 0}")
                                with col3:
                                    st.caption(f"Status: {tc['status'].upper()}")

                                st.write(f"**Preconditions**: {tc['preconditions']}")

                                # Steps table
                                st.write("**Steps**:")
                                for step_idx, step in enumerate(tc["steps"] if isinstance(tc["steps"], list) else []):
                                    if isinstance(step, dict):
                                        st.write(f"  {step.get('step_number', step_idx + 1)}. {step.get('action', '')}")
                                        st.caption(f"     → {step.get('expected_outcome', '')}")
                                    else:
                                        st.write(f"  {step_idx + 1}. {step}")

                                st.write(f"**Expected Result**: {tc['expected_result']}")

                                st.markdown("---")

                                # Review action buttons
                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    if st.button("✅ Approve", key=f"{tc_key}_approve"):
                                        success, error = update_test_case_review(tc["id"], "approved")
                                        if success:
                                            st.success("✅ Approved!")
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to approve: {error}")

                                with col2:
                                    if st.button("❌ Reject", key=f"{tc_key}_reject"):
                                        st.session_state.review_changes[f"{tc_key}_rejecting"] = True

                                with col3:
                                    if st.button("✏️ Edit", key=f"{tc_key}_edit"):
                                        st.session_state.review_changes[f"{tc_key}_editing"] = True

                                # Reject workflow
                                if st.session_state.review_changes.get(f"{tc_key}_rejecting"):
                                    reject_reason = st.text_area(
                                        "Rejection reason:",
                                        key=f"{tc_key}_reason"
                                    )
                                    if st.button("Confirm Rejection", key=f"{tc_key}_confirm_reject"):
                                        success, error = update_test_case_review(tc["id"], "rejected", reject_reason)
                                        if success:
                                            st.success("❌ Rejected!")
                                            st.session_state.review_changes[f"{tc_key}_rejecting"] = False
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to reject: {error}")

                                # Edit workflow
                                if st.session_state.review_changes.get(f"{tc_key}_editing"):
                                    edited_steps = st.text_area(
                                        "Edit test steps (one per line):",
                                        value="\n".join([
                                            f"{step.get('step_number', i+1)}. {step.get('action', '')}"
                                            for i, step in enumerate(tc["steps"] if isinstance(tc["steps"], list) else [])
                                        ]),
                                        key=f"{tc_key}_edit_steps"
                                    )
                                    edit_note = st.text_input(
                                        "Edit notes:",
                                        key=f"{tc_key}_edit_note"
                                    )
                                    if st.button("Save Changes", key=f"{tc_key}_confirm_edit"):
                                        success, error = update_test_case_review(tc["id"], "edited", edit_note, edited_steps)
                                        if success:
                                            st.success("✏️ Updated!")
                                            st.session_state.review_changes[f"{tc_key}_editing"] = False
                                            st.rerun()
                                        else:
                                            st.error(f"Failed to save: {error}")

                    else:
                        st.info("No test cases generated for this requirement.")

        else:
            st.info("No review data available. Run the pipeline first to generate items.")

        st.divider()
        st.markdown("""
        ### 🎯 Review Workflow

        1. **Approve ✅**: Accept the generated item as-is
        2. **Edit ✏️**: Modify the text/steps and mark as edited
        3. **Reject ❌**: Reject with explanation for regeneration

        ### 📝 Tips

        - Review acceptance criteria first - they inform test generation
        - Check for alignment between criteria and test cases
        - Ambiguous requirements (⚠️) may need tighter test coverage
        - You can edit any item without losing the original

        Ready to export? Head to the **Export** page! 👉
        """)
