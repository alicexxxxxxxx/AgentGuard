import ast

BLOCKED_MODULES = {"os", "subprocess", "sh", "pty", "commands"}
BLOCKED_CALLS = {"eval", "print", "exec"}

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

code = "import os\nprint('hello')"

tree = ast.parse(code)
print(tree)
auditor = SimpleAuditor()
auditor.visit(tree)

print(auditor.violations)
print(ast.dump(tree, indent=4))


