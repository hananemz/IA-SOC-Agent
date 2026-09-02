import os

p = r"C:\Users\lenovo\.agents\run_bench.js"
with open(p, "r", encoding="utf-8") as f:
    content = f.read()

# The broken path has: agents\.agents  (missing backslash before .agents)
# We need:             .agents
broken = "agents\\.agents"
fixed = ".agents"

count = content.count(broken)
print(f"Found {count} occurrences of broken pattern '{broken}'")

if count > 0:
    content = content.replace(broken, fixed)
    print("Replacement done")
else:
    # Debug: find the line that has rag_wrapper and show character codes
    for i, line in enumerate(content.splitlines()):
        if "rag_wrapper" in line:
            print(f"Line {i+1}: {repr(line)}")
            # Check byte by byte around 'agents' + '.agents'
            idx = line.find("agents")
            if idx > 0:
                snippet = line[idx:idx+30]
                print(f"Snippet from 'agents': {repr(snippet)}")
                for ch in snippet:
                    if ord(ch) < 32 or ord(ch) > 126:
                        print(f"  non-ASCII char at pos: ord={ord(ch)}")
            break

with open(p, "w", encoding="utf-8") as f:
    f.write(content)

print("File written")
