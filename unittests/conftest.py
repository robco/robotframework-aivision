import os
import sys


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

module = sys.modules.get("AIVision")
if module is not None:
    module_path = os.path.abspath(getattr(module, "__file__", ""))
    if not module_path.startswith(ROOT_DIR):
        del sys.modules["AIVision"]
