"""
Streamlit page for Jira bidirectional sync configuration and control.
"""

import os
import streamlit as st
import httpx
import json
from typing import Optional

# Page configuration MUST be first
st.set_page_config(
    page_title="Jira Sync",
    page_icon="🔄",
    layout="wide",
)

from utils.premium_ui import set_premium_theme

set_premium_theme()

# Check authentication
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.warning("🔐 Please log in first")
    st.switch_page("pages/0_Login.py")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.title("Jira Bidirectional Sync")

# Initialize session state
if "jira_config_updated" not in st.session_state:
    st.session_state.jira_config_updated = False

if "sync_in_progress" not in st.session_state:
    st.session_state.sync_in_progress = False

if "selected_project_id" not in st.session_state:
    st.session_state.selected_project_id = None


def load_projects():
    """Load list of projects from API."""
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{BACKEND_URL}/api/v1/projects",
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return []
    except Exception as e:
        st.error(f"Error loading projects: {e}")
        return []


def get_project_id():
    """Get current project ID from session state or selected project."""
    return st.session_state.get("selected_project_id") or st.session_state.get("current_project_id")


def get_api_base_url():
    """Get API base URL."""
    return BACKEND_URL


async def check_addon_enabled():
    """Check if Jira addon is enabled."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{get_api_base_url()}/api/v1/jira/status/test", timeout=5.0)
            return response.status_code != 404
    except:
        return False


def get_connection_status():
    """Get current Jira connection status."""
    project_id = get_project_id()
    if not project_id:
        return None
    
    try:
        with httpx.Client() as client:
            response = client.get(
                f"{get_api_base_url()}/api/v1/jira/status/{project_id}",
                timeout=10.0
            )
            if response.status_code == 200:
                return response.json()
            return None
    except Exception as e:
        st.error(f"Error fetching connection status: {e}")
        return None


def configure_jira_connection(config: dict) -> bool:
    """Configure Jira connection."""
    project_id = get_project_id()
    if not project_id:
        st.error("No project selected")
        return False
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{get_api_base_url()}/api/v1/jira/configure",
                params={"project_id": project_id},
                json=config,
                timeout=10.0
            )
            if response.status_code == 200:
                st.session_state.jira_config_updated = True
                return True
            else:
                st.error(f"Configuration failed: {response.text}")
                return False
    except Exception as e:
        st.error(f"Error configuring Jira: {e}")
        return False


def validate_connection() -> bool:
    """Validate and activate Jira connection."""
    project_id = get_project_id()
    if not project_id:
        st.error("No project selected")
        return False
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{get_api_base_url()}/api/v1/jira/validate",
                params={"project_id": project_id},
                timeout=10.0
            )
            if response.status_code == 200:
                return True
            else:
                st.error(f"Validation failed: {response.text}")
                return False
    except Exception as e:
        st.error(f"Error validating connection: {e}")
        return False


def perform_sync(sync_config: dict) -> bool:
    """Perform sync with Jira."""
    project_id = get_project_id()
    if not project_id:
        st.error("No project selected")
        return False
    
    st.session_state.sync_in_progress = True
    
    try:
        with httpx.Client() as client:
            response = client.post(
                f"{get_api_base_url()}/api/v1/jira/sync/{project_id}",
                json=sync_config,
                timeout=30.0
            )
            st.session_state.sync_in_progress = False
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, {"message": response.text}
    except Exception as e:
        st.session_state.sync_in_progress = False
        return False, {"message": str(e)}


def disconnect_jira() -> bool:
    """Disconnect Jira from project."""
    project_id = get_project_id()
    if not project_id:
        st.error("No project selected")
        return False
    
    try:
        with httpx.Client() as client:
            response = client.delete(
                f"{get_api_base_url()}/api/v1/jira/disconnect/{project_id}",
                timeout=10.0
            )
            if response.status_code == 200:
                return True
            else:
                st.error(f"Disconnection failed: {response.text}")
                return False
    except Exception as e:
        st.error(f"Error disconnecting: {e}")
        return False


# Main page content
# Add user navbar
from utils.premium_ui import add_user_navbar
add_user_navbar()
st.divider()

# Project selection
st.header("Select Project")

projects = load_projects()

if not projects:
    st.error("No projects found. Please upload a document first in the Upload page.")
    st.stop()

project_names = [p["name"] for p in projects]
selected_project_name = st.selectbox(
    "Select a project:",
    project_names,
    key="project_selectbox"
)

# Update session state with selected project
selected_project = next((p for p in projects if p["name"] == selected_project_name), None)
if selected_project:
    st.session_state.selected_project_id = selected_project["id"]

st.divider()

project_id = get_project_id()

if not project_id:
    st.info("📌 Please select a project first")
    st.stop()

# Status section
st.header("Connection Status")
status = get_connection_status()

if status:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Configured", "✓ Yes" if status["is_configured"] else "✗ No")
    
    with col2:
        st.metric("Active", "✓ Active" if status["is_active"] else "✗ Inactive")
    
    with col3:
        if status.get("jira_project_key"):
            st.metric("Project", status["jira_project_key"])
        else:
            st.metric("Project", "N/A")
    
    with col4:
        if status.get("last_sync_at"):
            st.metric("Last Sync", status["last_sync_at"])
        else:
            st.metric("Last Sync", "Never")
else:
    st.warning("Unable to fetch connection status")

st.divider()

# Configuration section
if not status or not status.get("is_active"):
    st.header("Configure Jira Connection")
    
    # Info box about credentials
    st.info(
        "🔒 **Credentials Security:** Your Jira email and API token are securely stored in the `.env` file on the server. "
        "Only the Jira URL and Project Key need to be configured here (they can change per project)."
    )
    
    with st.form("jira_config_form"):
        st.subheader("Jira Instance Details")
        
        jira_url = st.text_input(
            "Jira URL",
            placeholder="https://yourcompany.atlassian.net",
            help="Your Jira instance URL"
        )
        
        jira_project_key = st.text_input(
            "Project Key",
            placeholder="QUAL",
            help="Jira project key (e.g., QUAL, TEST, etc.)"
        )
        
        st.subheader("Sync Settings")
        
        sync_direction = st.selectbox(
            "Sync Direction",
            ["push", "pull", "bidirectional"],
            help="Push: Upload to Jira only\nPull: Download from Jira only\nBidirectional: Both ways"
        )
        
        submitted = st.form_submit_button("💾 Save Configuration", use_container_width=True)
        
        if submitted:
            if not all([jira_url, jira_project_key]):
                st.error("Please fill in Jira URL and Project Key")
            else:
                with st.spinner("Saving configuration..."):
                    config = {
                        "jira_url": jira_url,
                        "jira_project_key": jira_project_key,
                        "sync_direction": sync_direction
                    }
                    
                    if configure_jira_connection(config):
                        st.success("✓ Configuration saved")
                        
                        # Validate connection
                        with st.spinner("Validating connection..."):
                            if validate_connection():
                                st.success("✓ Connection validated and activated!")
                                st.rerun()
                            else:
                                st.error("✗ Connection validation failed. Check your Jira URL and credentials in .env")

else:
    # Active connection section
    st.header("Jira Connection Active")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Re-validate Connection", use_container_width=True):
            with st.spinner("Validating..."):
                if validate_connection():
                    st.success("✓ Connection validated")
                    st.rerun()
                else:
                    st.error("✗ Connection validation failed")
    
    with col2:
        if st.button("🔌 Disconnect Jira", use_container_width=True, type="secondary"):
            with st.spinner("Disconnecting..."):
                if disconnect_jira():
                    st.success("✓ Jira disconnected")
                    st.rerun()

st.divider()

# Sync section
if status and status.get("is_active"):
    st.header("Sync with Jira")
    
    with st.form("jira_sync_form"):
        st.subheader("What to Sync")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            include_requirements = st.checkbox(
                "Requirements",
                value=True,
                help="Sync requirements as Jira issues"
            )
        
        with col2:
            include_test_cases = st.checkbox(
                "Test Cases",
                value=True,
                help="Sync test cases as Jira issues"
            )
        
        with col3:
            include_criteria = st.checkbox(
                "Acceptance Criteria",
                value=True,
                help="Include acceptance criteria in sync"
            )
        
        sync_submitted = st.form_submit_button(
            "🚀 Start Sync",
            use_container_width=True,
            disabled=st.session_state.sync_in_progress
        )
        
        if sync_submitted:
            if not include_requirements and not include_test_cases:
                st.error("Select at least one item type to sync")
            else:
                sync_config = {
                    "include_requirements": include_requirements,
                    "include_test_cases": include_test_cases,
                    "include_criteria": include_criteria
                }
                
                with st.spinner("Syncing with Jira..."):
                    success, result = perform_sync(sync_config)
                    
                    if success:
                        st.success("✓ Sync completed successfully!")
                        
                        # Display results
                        result_col1, result_col2, result_col3 = st.columns(3)
                        
                        with result_col1:
                            st.metric(
                                "Items Synced",
                                result.get("items_synced", 0)
                            )
                        
                        with result_col2:
                            st.metric(
                                "Items Failed",
                                result.get("items_failed", 0)
                            )
                        
                        with result_col3:
                            if result.get("epic_key"):
                                st.metric(
                                    "Epic Created",
                                    result["epic_key"]
                                )
                    else:
                        st.error(f"Sync failed: {result.get('message', 'Unknown error')}")

else:
    st.info("📌 Configure and activate Jira connection to enable sync")

st.divider()

# Webhook section (for real-time sync from Jira back to Copilot)
if status and status.get("is_active"):
    st.header("Real-Time Webhook Sync")
    
    # Calculate webhook URL based on BACKEND_URL
    webhook_url = f"{BACKEND_URL}/api/v1/jira/webhooks/event"
    
    st.markdown("""
    ### Enable Real-Time Updates from Jira
    
    Configure a webhook in Jira to automatically sync status changes back to Copilot.
    When you update an issue in Jira, the changes will be reflected here instantly.
    """)
    
    # Display webhook URL in a copy-able box
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.text_input(
            "Webhook URL (Copy to Jira)",
            value=webhook_url,
            disabled=True,
            help="Copy this URL and paste it into Jira webhook configuration"
        )
    
    with col2:
        st.markdown("#### ")
        if st.button("📋 Copy", use_container_width=True, key="copy_webhook_url"):
            st.info(f"Webhook URL copied: {webhook_url}")
    
    st.markdown("---")
    
    # Webhook configuration instructions
    with st.expander("🔧 How to Configure Webhook in Jira"):
        st.markdown(f"""
        ### Step 1: Go to Jira Settings
        1. Open your Jira instance
        2. Click ⚙️ **Settings** → **System** → **Webhooks**
        
        ### Step 2: Create New Webhook
        1. Click **Create a webhook**
        2. Fill in the form:
           - **Name:** `Copilot Sync`
           - **URL:** `{webhook_url}`
           - **Events:** Select **Issue Updated**
        
        ### Step 3: Save and Test
        1. Click **Create**
        2. Change a synced issue status in Jira (e.g., KAN-5)
        3. Watch for the status change in Copilot
        
        ### Events to Monitor
        - ✅ **Issue Updated** (required) - Triggered when issue status/priority/assignee changes
        - ⚪ **Issue Created** (optional) - Triggered when new issue created
        
        [View detailed webhook setup guide →](../JIRA_WEBHOOK_SETUP.md)
        """)
    
    st.markdown("---")
    
    # Webhook status indicators
    st.subheader("Webhook Status")
    
    webhook_col1, webhook_col2 = st.columns(2)
    
    with webhook_col1:
        st.metric(
            "Webhook Status",
            "🟢 Ready",
            "Endpoint is listening for events"
        )
    
    with webhook_col2:
        st.metric(
            "Sync Direction",
            "📥 Pull",
            "Updates from Jira to Copilot"
        )

# Info section
st.divider()

with st.expander("ℹ️ About Jira Sync"):
    st.markdown("""
    ### Bidirectional Jira Sync
    
    This addon allows you to sync requirements and test cases with Jira automatically.
    
    **Features:**
    - 📤 **Push**: Export requirements and tests to Jira as issues
    - 📥 **Pull**: Import issue status changes back from Jira (Real-time webhooks)
    - 🔗 **Auto-linking**: Automatically link requirements to test cases
    - 🏛️ **Epic Organization**: Group synced items under a parent epic
    - 🔐 **Secure**: API tokens are encrypted before storage
    - ⚡ **Real-Time**: Webhook-based instant synchronization
    - 🗑️ **Reversible**: Can disconnect without affecting local data
    
    **Phase 1: Push Sync (✅ Completed)**
    - Export requirements to Jira as Story issues
    - Create parent epic for organization
    - Auto-link related items
    
    **Phase 2: Pull Sync (🔄 In Progress)**
    - Real-time webhooks from Jira to Copilot
    - Automatic status synchronization
    - Priority and assignee updates
    
    **Requirements:**
    - Active Jira Cloud instance
    - Project with appropriate issue types
    - API token with project write permissions
    - Network access to webhook endpoint
    
    **Best Practices:**
    1. Start with test data before syncing production requirements
    2. Create a dedicated epic for organized tracking
    3. Review auto-linked issues to ensure correct mapping
    4. Keep sync direction consistent with your workflow
    5. Configure webhook for real-time updates
    
    **Troubleshooting:**
    - If sync fails, check your Jira project key and permissions
    - Verify API token hasn't expired
    - Ensure Jira project has required issue types (Story, Task, Epic)
    - Check webhook configuration if updates aren't syncing back
    - View logs: `docker logs delivery-copilot-backend | grep webhook`
    
    **Security Note:**
    - Webhook endpoint currently accepts all events (development)
    - Production should add HMAC signature validation
    - Store webhook secret in encrypted environment variable
    """)
