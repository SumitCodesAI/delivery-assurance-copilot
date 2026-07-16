"""
Script to automatically create a capstone sample project in Streamlit UI
This script uploads all capstone documents as a complete project

Usage:
    python scripts/create_capstone_project.py
"""

import requests
import json
import os
from pathlib import Path


class CapstoneProjectCreator:
    """Creates a capstone sample project with all documents."""

    def __init__(self, backend_url="http://localhost:8000"):
        self.backend_url = backend_url
        self.session = requests.Session()
        self.project_id = None

    def check_backend(self):
        """Verify backend is running."""
        print("🔍 Checking if backend is running...")
        try:
            response = self.session.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend is running")
                return True
            else:
                print(f"❌ Backend returned status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot reach backend: {e}")
            print(f"   Make sure backend is running: docker-compose up -d")
            return False

    def create_project(self):
        """Create a new project."""
        print("\n📁 Creating capstone project...")

        data = {
            "name": "Capstone: Customer Onboarding System",
            "description": "Sample project demonstrating Requirements-to-Test extraction with RAG. Contains 8 documents covering BRD, functional requirements, API specs, NFR, SOP, QA policy, defect matrix, and change requests.",
        }

        try:
            response = self.session.post(
                f"{self.backend_url}/api/v1/projects",
                json=data,
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                self.project_id = result["id"]
                print(f"✅ Project created: {result['name']}")
                print(f"   Project ID: {self.project_id}")
                return True
            else:
                print(f"❌ Failed to create project: {response.text}")
                return False

        except Exception as e:
            print(f"❌ Error creating project: {e}")
            return False

    def upload_documents(self):
        """Upload all capstone documents."""
        print("\n📤 Uploading capstone documents...")

        docs_dir = Path(__file__).parent.parent / "capstone_data" / "docs"

        if not docs_dir.exists():
            print(f"❌ Documents directory not found: {docs_dir}")
            return False

        # Get all markdown files
        doc_files = sorted(list(docs_dir.glob("*.md")))

        if not doc_files:
            print(f"❌ No markdown files found in {docs_dir}")
            return False

        print(f"   Found {len(doc_files)} documents to upload")

        uploaded = 0
        for doc_file in doc_files:
            try:
                with open(doc_file, "rb") as f:
                    files = {"file": (doc_file.name, f, "text/markdown")}

                    response = self.session.post(
                        f"{self.backend_url}/api/v1/projects/{self.project_id}/upload",
                        files=files,
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        print(f"✅ {doc_file.name}")
                        print(f"   └─ ID: {result['id']}")
                        print(f"   └─ Status: {result['status']}")
                        uploaded += 1
                    else:
                        print(f"❌ {doc_file.name}: {response.text}")

            except Exception as e:
                print(f"❌ Error uploading {doc_file.name}: {e}")

        print(f"\n✅ Uploaded {uploaded}/{len(doc_files)} documents")
        return uploaded == len(doc_files)

    def get_project_status(self):
        """Get project status."""
        try:
            response = self.session.get(
                f"{self.backend_url}/api/v1/projects/{self.project_id}",
                timeout=10
            )

            if response.status_code == 200:
                result = response.json()
                print(f"\n📊 Project Status:")
                print(f"   Name: {result['name']}")
                print(f"   Documents: {result['document_count']}")
                print(f"   Status: {result['status']}")
                print(f"   Created: {result['created_at']}")
                return True

        except Exception as e:
            print(f"⚠️  Could not get project status: {e}")

    def run(self):
        """Run the complete project creation."""
        print("=" * 70)
        print("Capstone Project Creator")
        print("=" * 70)

        if not self.check_backend():
            return False

        if not self.create_project():
            return False

        if not self.upload_documents():
            return False

        self.get_project_status()

        print("\n" + "=" * 70)
        print("✅ Capstone project created successfully!")
        print("=" * 70)
        print("\n📝 Next steps:")
        print(f"   1. Open Streamlit: http://localhost:8501")
        print(f"   2. Go to 'Requirements' page")
        print(f"   3. Select project: 'Capstone: Customer Onboarding System'")
        print(f"   4. Click 'Run Pipeline' button")
        print(f"   5. Wait for extraction to complete")
        print(f"   6. Review generated requirements and tests")
        print(f"   7. Go to 'Review' page to approve/edit items")
        print(f"   8. Go to 'Export' page to download CSV/JSON")
        print("\n")

        return True


def main():
    creator = CapstoneProjectCreator()
    success = creator.run()
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
