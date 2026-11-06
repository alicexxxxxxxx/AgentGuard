# AgentGuard

An AST-powered static analysis gateway and real-time human-in-the-loop authorization middleware for securing AI-generated code execution.

---

## Overview

AgentGuard sits between AI code-generation agents and local system execution environments. It parses Python syntax trees in real time, flags dangerous system/process/network calls, and gates high-risk operations behind live WebSocket authorization prompts sent to a web dashboard.

```text
[AI Agent] ──(HTTP POST)──> [AgentGuard Gateway]
                                   │
                         1. Run AST Static Check
                                   │
                       High-Risk Code Detected?
                       ├── NO  ──> Execute & Return Result
                       └── YES ──> 2. Pause Request (asyncio.Event)
                                   3. Broadcast WebSocket Alert ──> [Web Dashboard]
                                                                         │
                                                                   Human Approval
                                                                         │
                       4. Unpause Endpoint & Return Decision <───────────┘