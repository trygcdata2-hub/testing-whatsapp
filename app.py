import sys
from pathlib import Path
import runpy

# Root entrypoint bridge to src/app.py
_repo_root = Path(__file__).resolve().parent

if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

target_app = _repo_root / "src" / "app.py"
runpy.run_path(str(target_app), run_name="__main__")
