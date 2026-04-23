
import os

scripts_dir = 'scripts'
src_dir = os.path.join('..', 'src')

patch = f"""import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '{src_dir}')))
"""

for filename in os.listdir(scripts_dir):
    if filename.endswith('.py'):
        filepath = os.path.join(scripts_dir, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'sys.path.append' not in content:
            new_content = patch + "\n" + content
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Patched {filename}")
