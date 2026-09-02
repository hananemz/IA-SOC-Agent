import re

p = r"C:\Users\lenovo\.agents\run_bench.js"
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "RAG_WRAPPER" in line and "agents\\.agents" in line:
        lines[i] = "const RAG_WRAPPER = 'C:\\\\Users\\\\lenovo\\\\.agents\\\\rag_wrapper.py';\n"
        print(f"Fixed line {i+1}: {lines[i].strip()}")
    elif "RAG_WRAPPER" in line:
        print(f"Line {i+1} already OK or mismatch: {line.strip()}")

# Fix padEnd on numbers: replace .padEnd( with .toString().padEnd(
for i, line in enumerate(lines):
    if ".padEnd(" in line:
        # Ensure toString() is called before padEnd
        lines[i] = line.replace(".padEnd(", ".toString().padEnd(")
        print(f"Applied toString() to line {i+1}")

with open(p, "w", encoding="utf-8") as f:
    f.writelines(lines)

print("All fixes applied. Checking file...")

# Verify
with open(p, "r", encoding="utf-8") as f:
    content = f.read()
broken = content.count("agents\\.agents")
print(f"remaining 'agents\\.agents' occurrences: {broken}")
rag_line = [l for l in content.split("\n") if "RAG_WRAPPER" in l]
print(f"RAG_WRAPPER line(s): {rag_line}")
