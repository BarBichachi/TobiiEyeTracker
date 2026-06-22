import os
import sys

# Ensure the project root is importable so tests can `from core import ...`
# (core/ and ui/ are namespace packages without __init__.py).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
