import sys
import os

# Add ai_engine and ai_engine/modules to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai_engine", "modules")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ai_engine")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

