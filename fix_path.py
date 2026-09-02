import re
p = r"C:\Users\lenovo\.agents\run_bench.js"
c = open(p, "r", encoding="utf-8").read()
old = r"C:\Users\lenovo\agents\.agents\rag_wrapper.py"
new = r"C:\Users\lenovo\.agents\rag_wrapper.py"
c = c.replace(old, new)
open(p, "w", encoding="utf-8").write(c)
print("RAG_WRAPPER path fix applied")
print("Contains agents\\.agents:", r"agents\.agents" in open(p).read())
