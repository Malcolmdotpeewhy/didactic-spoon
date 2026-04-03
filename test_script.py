with open("src/ui/components/draggable_list.py", "r") as f:
    lines = f.readlines()

# Print line number where indentation mismatch happens
for i, line in enumerate(lines):
    if line.strip():
        spaces = len(line) - len(line.lstrip(' '))
        if spaces % 4 != 0:
            print(f"Line {i+1}: {spaces} spaces")
