import os
import sys

# Get absolute path of the project root directory
project_root = os.path.dirname(os.path.abspath(__file__))

# Add both the project root and src directory to Python path
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

from src.main_ver2 import main

if __name__ == "__main__":
    main()
