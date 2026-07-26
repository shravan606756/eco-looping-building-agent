import os
import stat
import shutil
import warnings
from pathlib import Path
from typing import Dict, Any

from config import (
    ORIGINAL_IDF,
    WORKING_IDF,
    WORKING_DIR,
    OUTPUT_DIR,
    ROOT_DIR,
)


def _remove_readonly(func, path, exc_info):
    os.chmod(path, stat.S_IWRITE)
    try:
        func(path)
    except Exception as e:
        warnings.warn(f"Could not remove {path}: {e}")


class WorkspaceReset:

    def __init__(self):
        self.logs_dir = ROOT_DIR / "logs"
        self.archive_dir = ROOT_DIR / "logs_archive"
        from config import OPTIMIZED_DIR
        self.optimized_dir = OPTIMIZED_DIR

    def reset_workspace(self) -> Dict[str, Any]:
        result = {
            "status": "success",
            "actions": []
        }

        # 1. Delete all logs
        if self.logs_dir.exists():
            shutil.rmtree(self.logs_dir, onerror=_remove_readonly)
            result["actions"].append("Deleted logs/ directory")
        
        if self.archive_dir.exists():
            shutil.rmtree(self.archive_dir, onerror=_remove_readonly)
            result["actions"].append("Deleted logs_archive/ directory")

        # 2. Clean output directory
        if OUTPUT_DIR.exists():
            shutil.rmtree(OUTPUT_DIR, onerror=_remove_readonly)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        result["actions"].append("Cleaned output directory data/outputs/")

        # 3. Clean optimized directory
        if self.optimized_dir.exists():
            shutil.rmtree(self.optimized_dir, onerror=_remove_readonly)
        self.optimized_dir.mkdir(parents=True, exist_ok=True)
        result["actions"].append("Cleaned optimized IDF directory data/idf/optimized/")

        # 4. Restore working IDF from original IDF
        if WORKING_DIR.exists():
            shutil.rmtree(WORKING_DIR, onerror=_remove_readonly)
        WORKING_DIR.mkdir(parents=True, exist_ok=True)

        if not ORIGINAL_IDF.exists():
            raise FileNotFoundError(f"Original IDF file missing at: {ORIGINAL_IDF}")

        shutil.copy2(ORIGINAL_IDF, WORKING_IDF)
        result["actions"].append(f"Restored working IDF from {ORIGINAL_IDF.name}")

        return result