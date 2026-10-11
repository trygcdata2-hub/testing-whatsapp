import sys
from pathlib import Path
import runpy

# Compatibility bridge for Cloud deployments targeting project/src/app.py
_current_file = Path(__file__).resolve()
_repo_root = _current_file.parent.parent.parent

if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

target_app = _repo_root / "src" / "app.py"
runpy.run_path(str(target_app), run_name="__main__")
