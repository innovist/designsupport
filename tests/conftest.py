import sys
import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///./test_runtime_smoke.db"
os.environ["UPLOAD_DIR"] = "./test_uploads"
