"""
Streamlit page for document upload and project management.
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


def create_project(name: str, description: str = ""):
    """Create new project."""
    try:
        response = httpx.post(
            f"{BACKEND_URL}/api/v1/projects",
            json={"name": name, "description": description},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error creating project: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error creating project: {str(e)}")
        return None


def upload_document(project_id: str, file):
    """Upload document to project."""
    try:
        files = {"file": (file.name, file.getvalue(), file.type)}
        response = httpx.post(
            f"{BACKEND_URL}/api/v1/projects/{project_id}/upload",
            files=files,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error uploading document: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error uploading document: {str(e)}")
        return None


def load_project_documents(project_id: str):
    """Load documents for a project."""
    try:
        response = httpx.get(
            f"{BACKEND_URL}/api/v1/projects/{project_id}/documents",
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error loading documents: {str(e)}")
        return []


def delete_project(project_id: str):
    """Delete a project and all its associated data."""
    try:
        response = httpx.delete(
            f"{BACKEND_URL}/api/v1/projects/{project_id}",
            timeout=10
        )
        if response.status_code == 200:
            return True
        else:
            st.error(f"Error deleting project: {response.text}")
            return False
    except Exception as e:
        st.error(f"Error deleting project: {str(e)}")
        return False


# Add user navbar
from utils.premium_ui import add_user_navbar
add_user_navbar()
st.divider()

# Page title and description
st.title("Upload Documents")
st.markdown("Upload BRDs, user stories, API specs, and other requirement documents for processing.")

# Initialize session state
if "selected_project" not in st.session_state:
    st.session_state.selected_project = None

if "refresh_projects" not in st.session_state:
    st.session_state.refresh_projects = False

if "show_delete_confirmation" not in st.session_state:
    st.session_state.show_delete_confirmation = False


# Project management section
st.subheader("Project Management")

col1, col2 = st.columns([2, 1])

with col1:
    # Load existing projects
    projects = load_projects()
    project_names = [p["name"] for p in projects]

    selected_project_name = st.selectbox(
        "Select or create a project:",
        options=project_names + ["[+ Create New Project]"],
        key="project_selector"
    )

    if selected_project_name == "[+ Create New Project]":
        st.session_state.selected_project = None

with col2:
    if st.button("Refresh"):
        st.rerun()


# Create new project section
if selected_project_name == "[+ Create New Project]":
    st.divider()
    st.subheader("Create New Project")

    project_name = st.text_input("Project Name:", placeholder="e.g., Mobile App v2.0")
    project_desc = st.text_area("Description (optional):", placeholder="Brief description of your project")

    if st.button("✅ Create Project"):
        if project_name:
            new_project = create_project(project_name, project_desc)
            if new_project:
                st.success(f"✅ Project '{project_name}' created successfully!")
                st.session_state.selected_project = new_project["id"]
                st.session_state.refresh_projects = True
                st.rerun()
        else:
            st.error("Please enter a project name")


# Upload documents section
elif selected_project_name and selected_project_name != "[+ Create New Project]":
    # Find selected project
    selected_project = next(
        (p for p in projects if p["name"] == selected_project_name),
        None
    )

    if selected_project:
        st.session_state.selected_project = selected_project["id"]

        st.divider()
        st.subheader(f"Project: {selected_project['name']}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Documents", selected_project.get("document_count", 0))
        with col2:
            st.metric("Status", selected_project.get("status", "unknown"))
        with col3:
            st.metric("Created", selected_project.get("created_at", "").split("T")[0])
        with col4:
            if st.button("Delete Project", key="delete_btn", help="Permanently delete this project and all its data"):
                st.session_state.show_delete_confirmation = True
                st.rerun()

        st.divider()

        # Document upload section
        st.subheader("Upload Documents")
        st.write("Supported formats: PDF, DOCX, TXT")

        uploaded_files = st.file_uploader(
            "Choose files to upload:",
            type=["pdf", "docx", "txt", "doc"],
            accept_multiple_files=True,
            help="You can select multiple files at once"
        )

        if uploaded_files:
            if st.button("🚀 Upload Files"):
                progress_bar = st.progress(0)
                status_container = st.empty()

                for idx, file in enumerate(uploaded_files):
                    status_container.write(f"Uploading {idx + 1}/{len(uploaded_files)}: {file.name}")
                    result = upload_document(str(selected_project["id"]), file)

                    if result:
                        status_container.success(f"✅ Uploaded: {file.name} ({result.get('chunk_count', 0)} chunks)")
                    else:
                        status_container.error(f"❌ Failed to upload: {file.name}")

                    progress = (idx + 1) / len(uploaded_files)
                    progress_bar.progress(progress)

                st.success("✅ Upload complete!")
                st.rerun()

        st.divider()

        # Delete confirmation dialog
        if st.session_state.show_delete_confirmation:
            st.warning(
                f"⚠️ **WARNING**: You are about to permanently delete the project '{selected_project['name']}' "
                f"and ALL its associated data (documents, requirements, test cases, embeddings, Jira mappings). "
                f"This action **cannot be undone**."
            )
            col1, col2, col3 = st.columns([1, 1, 2])
            with col1:
                if st.button("✅ Yes, Delete Everything", key="confirm_delete"):
                    if delete_project(str(selected_project["id"])):
                        st.success("✅ Project deleted successfully!")
                        st.session_state.selected_project = None
                        st.session_state.show_delete_confirmation = False
                        st.session_state.refresh_projects = True
                        st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_delete"):
                    st.session_state.show_delete_confirmation = False
                    st.rerun()
            st.divider()

        # List existing documents
        st.subheader("Uploaded Documents")

        documents = load_project_documents(str(selected_project["id"]))

        if documents:
            # Create a nice table
            doc_data = []
            for doc in documents:
                doc_data.append({
                    "📄 Filename": doc["filename"],
                    "Type": doc["doc_type"].upper(),
                    "Chunks": f'{doc["chunk_count"]}',
                    "Status": "✅ Indexed" if doc["status"] == "indexed" else f"⏳ {doc['status'].capitalize()}",
                    "Uploaded": doc["uploaded_at"].split("T")[0],
                })

            st.dataframe(
                doc_data,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("No documents uploaded yet. Use the upload section above to add documents.")

        st.divider()

        # Next step
        st.info("📝 Next Step: Go to the **Requirements** page to run the AI pipeline and extract requirements!")


else:
    st.info("👈 Select or create a project to get started")

st.divider()
st.markdown("""
### 💡 Tips for Better Results

- **Document Quality**: Use clear, well-formatted documents for better parsing
- **Multiple Docs**: Upload related BRD, API specs, and QA policy documents together for better context
- **Document Types**: Label documents correctly (PDF for BRD, DOCX for user stories, etc.)
- **Large Files**: Files over 20MB will be rejected - split large documents if needed
- **Chunking**: Documents are automatically split into 512-token chunks for processing

### ⚙️ How It Works

1. Files are uploaded to the server
2. Documents are parsed (text extraction from PDF/DOCX/TXT)
3. Content is split into overlapping chunks (512 tokens, 50-token overlap)
4. Chunks are embedded using sentence-transformers
5. Embeddings are stored in ChromaDB for retrieval

Ready? Upload your documents above and proceed to the **Requirements** page! 🎯
""")
