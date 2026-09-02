p = r"C:\Users\lenovo\.agents\run_bench.js"
with open(p, "r", encoding="utf-8") as f:
    content = f.read()

# In the JS file, backslashes in strings are written as \\
# Broken: agents\\.agents  (missing lenovo\\. then agents)
# The broken literal in the file is literally: agents\\.agents
broken = "agents\\\\.agents"
fixed = ".agents"

count = content.count(broken)
print(f"Found {count} occurrences of broken pattern '{broken}'")

if count == 0:
    # Try without extra escaping
    for pattern in [
        "agents\\.agents",
        "agents\\\\\\.agents",
    ]:
        c = content.count(pattern)
        print(f"  Trying '{pattern}': found {c}")

# Just fix line 9 directly
lines = content.splitlines()
print(f"Line 9 before: {repr(lines[8])}")

# Find and fix the RAG_WRAPPER line
for i, line in enumerate(lines):
    if "RAG_WRAPPER" in line and "const" in line:
        lines[i] = "const RAG_WRAPPER = 'C:\\\\Users\\\\lenovo\\\\.agents\\\\rag_wrapper.py';"
        print(f"Fixed line {i+1}: {repr(lines[i])}")

with open(p, "w", encoding="utf-8") as f:
    f.write("\\n".join(lines))

print("File written. Verifying...")
with open(p, "r", encoding="utf-8") as f:
    check = f.read()
rag_lines = [l for l in check.splitlines() if "RAG_WRAPPER" in l and "const" in l]
print(f"RAG_WRAPPER line: {rag_lines}")
print(f"Has agents\\.agents: {'agents' + chr(92) + '.agents' in check}")
