"""
File handling utilities — audio, document export.
"""
import os
import uuid


def unique_filename(extension: str) -> str:
    """Generate a unique filename with the given extension."""
    return f'{uuid.uuid4().hex}.{extension.lstrip(".")}'


def safe_path(folder: str, filename: str) -> str:
    """Return an absolute path, creating the folder if needed."""
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, filename)


def cleanup_file(path: str):
    """Delete a file if it exists. Used for temp upload cleanup."""
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
