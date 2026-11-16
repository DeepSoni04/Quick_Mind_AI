import sys
import os

# Ensure current directory is on python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from app.main import app
    print("FastAPI ASGI app compiled successfully")
except Exception as e:
    import traceback
    print("VALIDATION ERROR CAUGHT:", file=sys.stderr)
    traceback.print_exc()
    sys.exit(1)

