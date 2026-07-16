"""
Main Streamlit application entry point.
Redirects to login if not authenticated, otherwise shows dashboard.
"""

import streamlit as st
from utils.premium_ui import set_premium_theme

set_premium_theme()

# Apply Finesse theme background
st.markdown("""
    <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #f0e7ff 0%, #e0e7ff 50%, #dbeafe 100%) !important;
        }
    </style>
""", unsafe_allow_html=True)

# Check authentication first - redirect to login if not authenticated
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.switch_page("pages/0_Login.py")

# If authenticated, show dashboard
from utils.premium_ui import add_user_navbar

add_user_navbar()
st.divider()

st.title("Delivery Assurance Copilot")
st.markdown("""
Welcome to **Delivery Assurance Copilot**!

This platform helps you:
- Extract requirements from documents
- Generate acceptance criteria and test cases
- Review and approve artifacts
- Export traceability matrices
- Integrate with Jira

### Getting Started

1. **Upload Documents** - Start by uploading your requirements documents
2. **Run Pipeline** - Extract requirements and generate tests automatically
3. **Review** - Approve or reject generated items
4. **Export** - Download your traceability matrix as CSV or JSON

---

### How It Works

Documents → Parser → Chunks → RAG Chain → LangGraph → Test Artifacts → Export

---

### Features

✓ AI-Powered intelligent analysis
✓ RAG integration for standards retrieval
✓ Complete requirements to test coverage mapping
✓ Bidirectional Jira sync
✓ Comprehensive test coverage
✓ Advanced analytics and metrics

---

Ready to get started? Click on **Upload** to begin processing your documents!
""")
