import ast
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import List, Dict

app = FastAPI()

BLOCKED_MODULES = {"os", "subprocess", "sh", "pty", "commands"}
BLOCKED_CALLS = {"eval", "print", "exec"}

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.pending_events: Dict[str, asyncio.Event]= {}
        self.user_decision: Dict[str, bool] = {}

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.append(ws)
        print("New UI dashboard connected via WebSocket.")

    def disconnect(self, ws: WebSocket):
        self.active_connections.remove(ws)
        print("UI dashboard disconnected.")

    async def send_alert(self, data: dict):
        for ws in self.active_connections:
            await ws.send_json(data)

manager = ConnectionManager()

class CodePayload(BaseModel):
    request_id: str
    action_name: str
    code_snippet: str

class SimpleAuditor(ast.NodeVisitor):
    def __init__(self):
        self.violations = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name in BLOCKED_MODULES:
                self.violations.append(f"Forbidden import: {alias.name}")
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id in BLOCKED_CALLS:
            self.violations.append(f"Forbidden call '{node.func.id}()' at line {node.lineno}")
        self.generic_visit(node)

@app.post("/api/audit")
async def audit_code_endpoint(payload: CodePayload):
    tree = ast.parse(payload.code_snippet)
    auditor = SimpleAuditor()
    auditor.visit(tree)

    if len(auditor.violations) > 0:
        event = asyncio.Event()
        manager.pending_events[payload.request_id] = event

        await manager.send_alert({
            "type": "PERMISSION_REQUIRED",
            "request_id": payload.request_id,
            "action_name": payload.action_name,
            "violations": auditor.violations,
            "code_snippet": payload.code_snippet
        })

        try:
            await asyncio.wait_for(event.wait(), timeout=30.0)
        except asyncio.TimeoutError:
            manager.pending_events.pop(payload.request_id, None)
            raise HTTPException(status_code=408, detail='Approval request timed out')

        approved = manager.user_decision.pop(payload.request_id, False)
        manager.pending_events.pop(payload.request_id, None)

        if not approved:
            raise HTTPException(status_code=403, detail="Execution denied by user.")

    return {
        "status": "SUCCESS",
        "action": payload.action_name,
        "violations_overridden": auditor.violations
    }

@app.websocket("/ws/approval")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            req_id = data.get("request_id")
            approved = data.get("approved", False)

            if req_id in manager.pending_events:
                manager.user_decision[req_id] = approved
                manager.pending_events[req_id].set()
    except WebSocketDisconnect:
        manager.disconnect(ws)






