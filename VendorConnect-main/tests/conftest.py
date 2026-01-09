"""
Pytest configuration file.
This file is automatically loaded by pytest before running tests.
It configures the Python path so that imports work correctly.
"""

import sys
import os

# Add the parent directory (VendorConnect-main) to the Python path
# so that modules like 'ai_integrations' and 'app' can be imported
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
