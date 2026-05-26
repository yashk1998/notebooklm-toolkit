import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from notebooklm.config import LIBRARY_FILE, DATA_DIR


class NotebookLibrary:
    """Manages a local collection of NotebookLM notebooks with metadata."""

    def __init__(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.library_file = LIBRARY_FILE
        self.notebooks: Dict[str, Dict[str, Any]] = {}
        self.active_notebook_id: Optional[str] = None
        self._load_library()

    def _load_library(self):
        if self.library_file.exists():
            try:
                with open(self.library_file, "r") as f:
                    data = json.load(f)
                    self.notebooks = data.get("notebooks", {})
                    self.active_notebook_id = data.get("active_notebook_id")
            except Exception as e:
                print(f"Warning: Error loading library: {e}")
                self.notebooks = {}
                self.active_notebook_id = None
        else:
            self._save_library()

    def _save_library(self):
        try:
            data = {
                "notebooks": self.notebooks,
                "active_notebook_id": self.active_notebook_id,
                "updated_at": datetime.now().isoformat(),
            }
            with open(self.library_file, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving library: {e}")

    def add_notebook(
        self,
        url: str,
        name: str,
        description: str,
        topics: List[str],
        content_types: Optional[List[str]] = None,
        use_cases: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        notebook_id = name.lower().replace(" ", "-").replace("_", "-")
        if notebook_id in self.notebooks:
            raise ValueError(f"Notebook with ID '{notebook_id}' already exists")

        notebook = {
            "id": notebook_id,
            "url": url,
            "name": name,
            "description": description,
            "topics": topics,
            "content_types": content_types or [],
            "use_cases": use_cases or [],
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "use_count": 0,
            "last_used": None,
        }

        self.notebooks[notebook_id] = notebook
        if len(self.notebooks) == 1:
            self.active_notebook_id = notebook_id

        self._save_library()
        print(f"Added notebook: {name} ({notebook_id})")
        return notebook

    def remove_notebook(self, notebook_id: str) -> bool:
        if notebook_id not in self.notebooks:
            print(f"Notebook not found: {notebook_id}")
            return False

        del self.notebooks[notebook_id]
        if self.active_notebook_id == notebook_id:
            self.active_notebook_id = list(self.notebooks.keys())[0] if self.notebooks else None

        self._save_library()
        print(f"Removed notebook: {notebook_id}")
        return True

    def update_notebook(
        self,
        notebook_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        topics: Optional[List[str]] = None,
        content_types: Optional[List[str]] = None,
        use_cases: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        if notebook_id not in self.notebooks:
            raise ValueError(f"Notebook not found: {notebook_id}")

        nb = self.notebooks[notebook_id]
        for field, value in [
            ("name", name),
            ("description", description),
            ("topics", topics),
            ("content_types", content_types),
            ("use_cases", use_cases),
            ("tags", tags),
            ("url", url),
        ]:
            if value is not None:
                nb[field] = value

        nb["updated_at"] = datetime.now().isoformat()
        self._save_library()
        print(f"Updated notebook: {nb['name']}")
        return nb

    def get_notebook(self, notebook_id: str) -> Optional[Dict[str, Any]]:
        return self.notebooks.get(notebook_id)

    def list_notebooks(self) -> List[Dict[str, Any]]:
        return list(self.notebooks.values())

    def search_notebooks(self, query: str) -> List[Dict[str, Any]]:
        q = query.lower()
        return [
            nb
            for nb in self.notebooks.values()
            if any(
                q in field
                for field in [
                    nb["name"].lower(),
                    nb["description"].lower(),
                    " ".join(nb["topics"]).lower(),
                    " ".join(nb["tags"]).lower(),
                    " ".join(nb.get("use_cases", [])).lower(),
                ]
            )
        ]

    def select_notebook(self, notebook_id: str) -> Dict[str, Any]:
        if notebook_id not in self.notebooks:
            raise ValueError(f"Notebook not found: {notebook_id}")
        self.active_notebook_id = notebook_id
        self._save_library()
        nb = self.notebooks[notebook_id]
        print(f"Activated notebook: {nb['name']}")
        return nb

    def get_active_notebook(self) -> Optional[Dict[str, Any]]:
        if self.active_notebook_id:
            return self.notebooks.get(self.active_notebook_id)
        return None

    def increment_use_count(self, notebook_id: str) -> Dict[str, Any]:
        if notebook_id not in self.notebooks:
            raise ValueError(f"Notebook not found: {notebook_id}")
        nb = self.notebooks[notebook_id]
        nb["use_count"] += 1
        nb["last_used"] = datetime.now().isoformat()
        self._save_library()
        return nb

    def get_stats(self) -> Dict[str, Any]:
        total_topics: set = set()
        total_use_count = 0
        for nb in self.notebooks.values():
            total_topics.update(nb["topics"])
            total_use_count += nb["use_count"]

        most_used = (
            max(self.notebooks.values(), key=lambda n: n["use_count"])
            if self.notebooks
            else None
        )

        return {
            "total_notebooks": len(self.notebooks),
            "total_topics": len(total_topics),
            "total_use_count": total_use_count,
            "active_notebook": self.get_active_notebook(),
            "most_used_notebook": most_used,
            "library_path": str(self.library_file),
        }
