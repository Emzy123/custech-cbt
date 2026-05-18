"""
Local backend launcher that ensures the project import path is available.
"""

from pathlib import Path
import os
import sys

import uvicorn


def main() -> None:
    repo_root = Path(__file__).resolve().parent
    src_path = repo_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Preserve env overrides while providing safe defaults for local boot.
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() in {"1", "true", "yes"}

    uvicorn.run(
        "cbt.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=os.getenv("LOG_LEVEL", "info").lower(),
    )


if __name__ == "__main__":
    main()
