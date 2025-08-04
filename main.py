# main.py
# Entry point of the EyeTracker application.
# Delegates setup and execution to the core bootstrap module.

from core import bootstrap

if __name__ == "__main__":
    bootstrap.start()