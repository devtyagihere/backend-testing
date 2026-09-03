import sys
import os

# Ensure the root project directory is in the python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app.main import app

# Standard Mangum adapter for Vercel/AWS Lambda Serverless ASGI handling
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except Exception:
    handler = app

app = app
