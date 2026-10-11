import sys
from pathlib import Path
import runpy
import importlib

# Root entrypoint bridge to src/app.py
_repo_root = Path(__file__).resolve().parent

if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

# Clean cached src modules on hot-reload to guarantee fresh definitions
for mod_name in list(sys.modules.keys()):
    if mod_name.startswith("src.") or mod_name == "src":
        del sys.modules[mod_name]
importlib.invalidate_caches()

target_app = _repo_root / "src" / "app.py"
runpy.run_path(str(target_app), run_name="__main__")

