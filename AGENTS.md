# AGENTS.md — Agent Interface & Safety Guidelines

This document specifies the communication protocols, tool integration standards, and security constraints for AI agents (e.g., Claude Code, Cursor, custom LLM tool-calling loops) interacting with the AgentGuard gateway.

---

## 1. Core Operating Guidelines for AI Agents

1. **Mandatory Routing:** All generated Python code intended for system execution **must** be submitted to the AgentGuard gateway before local invocation.
2. **Handling Blocked Imports:** If the gateway flags forbidden imports (`os`, `subprocess`, `sys`, `shutil`, `ctypes`), do not attempt to bypass detection via dynamic string evaluation (`eval`, `exec`, `__import__`).
3. **Approval Timeouts:** High-risk code execution requires human authorization over WebSockets. The gateway enforces a strict 30-second timeout. If execution fails with HTTP 408 (Timeout) or HTTP 403 (Denied), explain the security denial clearly to the user rather than retrying in an automated loop.

---

## 2. API Specifications

### Security Audit Endpoint (`POST /api/audit`)
Perform non-blocking static code inspection without gating or execution.

* **Endpoint:** `POST http://localhost:8000/api/audit`
* **Headers:** `Content-Type: application/json`
* **Request Body:**
  ```json
  {
    "request_id": "req-unique-id",
    "action_name": "describe_action_intent",
    "code_snippet": "print('Hello, World!')"
  }