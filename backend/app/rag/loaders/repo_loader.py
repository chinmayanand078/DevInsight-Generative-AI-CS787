import os

def load_repo_text(base_path: str = "."):
    """
    Reads repo documentation files (README + docs/*.md) into a list of (content, metadata)
    """
    targets = []

    # 1. README.md
    readme_path = os.path.join(base_path, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            targets.append((f.read(), {"source": "README.md"}))

    # 2. docs/*.md
    docs_dir = os.path.join(base_path, "docs")
    if os.path.exists(docs_dir):
        for filename in os.listdir(docs_dir):
            if filename.endswith(".md"):
                path = os.path.join(docs_dir, filename)
                with open(path, "r", encoding="utf-8") as f:
                    targets.append((f.read(), {"source": f"docs/{filename}"}))

    return targets

