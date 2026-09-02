const { execSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const WS = process.cwd();
const pyFile = path.join(WS, "gen_report.py");

console.log("Running gen_report.py with py...");
try {
  const out = execSync("py " + pyFile, { timeout: 60000, encoding: "utf-8", maxBuffer: 10 * 1024 * 1024 });
  console.log(out);
  console.log("SUCCESS");
} catch (e) {
  console.log("Error running gen_report.py:");
  console.log(e.message.slice(0, 500));
  console.log("STDERR:", e.stderr ? e.stderr.toString().slice(0, 500) : "none");
}
