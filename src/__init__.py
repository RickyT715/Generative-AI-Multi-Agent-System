import os
from pathlib import Path

# Set HF_HOME before any library imports to avoid ~/.cache/huggingface permission
# issues on Windows. Must run before huggingface_hub is imported anywhere.
os.environ.setdefault(
    "HF_HOME", str(Path(__file__).resolve().parent.parent / ".hf_cache")
)
