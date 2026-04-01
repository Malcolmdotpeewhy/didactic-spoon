import os
import re

for root, dirs, files in os.walk('src/ui'):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Simple check for missing hand2 cursor on CTkButton/CTkOptionMenu
            print(f"Checking {filepath}...")
