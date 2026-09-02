import re
path = r"C:\Users\lenovo\.agents\run_bench.js"
c = open(path, "r", encoding="utf-8").read()
c = c.replace("agents\\.agents", ".agents")
c = c.replace(".padEnd(", ".toString().padEnd(")
open(path, "w", encoding="utf-8").write(c)
print("Fixes applied OK")
