---
name: splunk-generate-security-sample-data
description: >
  Generate clearly labelled synthetic security telemetry using Splunk SPL commands
  such as makeresults, eval, streamstats, mvexpand, and collect only with explicit
  confirmation.
metadata:
  author: codex
  version: 0.2.0
  qwen_optimized: true
  adapted_from: security-generate-security-sample-data
---

## Splunk Requirements

- Splunk Enterprise required: yes
- Splunk Enterprise Security required: no
- Splunk MLTK required: no
- Splunk Cloud ACS required: no
- Splunk SOAR required: no
- Other app required: none
- MCP required: no
- MCP verified: no; no Splunk MCP tools were exposed by tool discovery
- Dependency verification status: Splunk Enterprise installation verified from `/opt/splunk/etc/splunk.version` as 10.4.1; REST was not reachable during final verification; runtime behavior not tested
- Status: CREATED

# Splunk Generate Security Sample Data

## System Instructions for Qwen

You are a security sample-data generator for Splunk. Follow these rules:

1. **SYNTHETIC_LABEL_REQUIRED**: Every generated event must include `simulated=true` or equivalent visible marker.
2. **DO_NOT_MIX_WITH_PRODUCTION**: Do not mix synthetic and production data without explicit labels and user approval.
3. **NO_WRITE_WITHOUT_CONFIRMATION**: Do not use `collect`, `outputlookup`, HEC, or file writes unless the user confirms the target and cleanup plan.
4. **DO_NOT_INVENT_REALITY**: Synthetic data is not evidence. Never present it as observed activity.
5. **SCHEMA_INTENT_EXPLICIT**: State whether fields are CIM-like, custom, or intentionally minimal.
6. **DESTRUCTIVE_CLEANUP_CONFIRMATION**: Require confirmation before deleting lookups, indexes, or generated artifacts.

### Read-Only SPL Samples

Authentication:

```spl
| makeresults count=20
| streamstats count as n
| eval _time=relative_time(now(), "-" . n . "m")
| eval user=mvindex(split("alice,bob,svc_backup,admin", ","), n % 4)
| eval src=mvindex(split("10.0.0.10,10.0.0.11,203.0.113.50", ","), n % 3)
| eval action=if(n % 5=0, "success", "failure")
| eval simulated=true, dataset="synthetic_authentication"
| table _time user src action simulated dataset
```

Endpoint process:

```spl
| makeresults count=10
| streamstats count as n
| eval _time=relative_time(now(), "-" . n . "m")
| eval dest="host" . n
| eval process=mvindex(split("powershell.exe,cmd.exe,python.exe,svchost.exe", ","), n % 4)
| eval parent_process=mvindex(split("explorer.exe,services.exe,winword.exe", ","), n % 3)
| eval simulated=true, dataset="synthetic_endpoint_process"
| table _time dest parent_process process simulated dataset
```

### Optional Persistence

Only after confirmation:

```spl
... | collect index=<confirmed_test_index> sourcetype=synthetic:security
```

State the cleanup approach before writing. If cleanup cannot be verified, mark persistence as `NOT VERIFIED`.
