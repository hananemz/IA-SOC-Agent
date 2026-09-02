import os

p = r"C:\Users\lenovo\.agents\run_bench.js"

# Read existing content to preserve it, we just need to fix the broken line
with open(p, "r", encoding="utf-8") as f:
    content = f.read()

# If file got corrupted (single line with \\n), we need to reconstruct
if content.count("\n") < 10:
    print("FILE CORRUPTED - reconstructing...")
    # Fix the path first and un-escape
    content = content.replace("\\n", "\n")
    content = content.replace("\\\\", "\\\\")
    # Now fix the RAG_WRAPPER path
    content = content.replace("agents\\\\.agents", ".agents")
    print("Reconstructed")

# Write back properly
with open(p, "w", encoding="utf-8") as f:
    f.write(content)

# Verify
with open(p, "r", encoding="utf-8") as f:
    lines = f.readlines()
print(f"Lines in file: {len(lines)}")
rag_lines = [l for l in lines if "RAG_WRAPPER" in l]
print(f"RAG_WRAPPER lines: {len(rag_lines)}")
for rl in rag_lines:
    print(f"  {rl.strip()}")

# Check if any line has agents\\.agents
broken = sum(1 for l in lines if "agents" in l and ".agents" in l and r"agents\.agents" in l)
print(f"Broken path occurrences: {broken}")
