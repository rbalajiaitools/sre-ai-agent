"""Fix indentation in real.py for background task."""

# Read the file
with open('app/api/real.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line where we need to start indenting (after "agent_results = []")
# and stop indenting (before the except block for background function)
start_indent = False
output_lines = []

for i, line in enumerate(lines):
    # Start indenting after "agent_results = []" in the background function
    if i > 680 and "agent_results = []" in line and not start_indent:
        output_lines.append(line)
        start_indent = True
        continue
    
    # Stop indenting at the except block for background function
    if start_indent and i > 1100 and line.strip().startswith("# Update investigation with agent results"):
        start_indent = False
    
    # Add indentation if we're in the section
    if start_indent and line.strip() and not line.startswith('            '):
        # Add 4 spaces of indentation
        if line.startswith('        '):
            line = '    ' + line
        elif line.startswith('    '):
            line = '        ' + line
    
    output_lines.append(line)

# Write back
with open('app/api/real.py', 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print("Indentation fixed!")
