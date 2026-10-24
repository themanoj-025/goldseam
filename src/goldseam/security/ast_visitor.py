"""AST visitor for static policy checking, forbidden call detection, and dunder traversal inspection."""

import ast

from pydantic import BaseModel, ConfigDict

from goldseam.security.import_policy import SecurityPolicy


class ASTFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    line: int
    column: int
    rule: str
    message: str
    severity: str = "ERROR"


class SecurityASTVisitor(ast.NodeVisitor):
    def __init__(self, policy: SecurityPolicy, preset: str = "strict") -> None:
        self.policy = policy
        self.preset = preset
        self.findings: list[ASTFinding] = []
        self.imported_modules: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            mod_name = alias.name
            self.imported_modules.append(mod_name)
            if not self.policy.is_module_allowed(mod_name, self.preset):
                self.findings.append(
                    ASTFinding(
                        line=node.lineno,
                        column=node.col_offset,
                        rule="FORBIDDEN_IMPORT",
                        message=f"Import of module '{mod_name}' is not allowed under preset '{self.preset}'",
                    )
                )
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        mod_name = node.module or ""
        if mod_name == "sys":
            allowed_sys_symbols = {"stdin", "stdout", "stderr", "exit"}
            for alias in node.names:
                if alias.name not in allowed_sys_symbols:
                    self.findings.append(
                        ASTFinding(
                            line=node.lineno,
                            column=node.col_offset,
                            rule="FORBIDDEN_IMPORT",
                            message=f"Import of symbol '{alias.name}' from 'sys' is forbidden; only {allowed_sys_symbols} are permitted",
                        )
                    )
            self.imported_modules.append(mod_name)
            self.generic_visit(node)
            return

        if mod_name:
            self.imported_modules.append(mod_name)
            if not self.policy.is_module_allowed(mod_name, self.preset):
                self.findings.append(
                    ASTFinding(
                        line=node.lineno,
                        column=node.col_offset,
                        rule="FORBIDDEN_IMPORT",
                        message=f"Import from module '{mod_name}' is not allowed under preset '{self.preset}'",
                    )
                )
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id == "__builtins__":
            self.findings.append(
                ASTFinding(
                    line=node.lineno,
                    column=node.col_offset,
                    rule="FORBIDDEN_NAME",
                    message="Direct reference to '__builtins__' is strictly prohibited",
                )
            )
        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript) -> None:
        # Catch dict index like obj['__class__'] or __builtins__['eval']
        key_str = ""
        if isinstance(node.slice, ast.Constant) and isinstance(node.slice.value, str):
            key_str = node.slice.value
        if key_str in self.policy.forbidden_calls or key_str in self.policy.forbidden_attributes:
            self.findings.append(
                ASTFinding(
                    line=node.lineno,
                    column=node.col_offset,
                    rule="FORBIDDEN_SUBSCRIPT",
                    message=f"Subscript access to forbidden member '{key_str}'",
                )
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func_name = ""
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name in self.policy.forbidden_calls:
            self.findings.append(
                ASTFinding(
                    line=node.lineno,
                    column=node.col_offset,
                    rule="FORBIDDEN_CALL",
                    message=f"Call to forbidden function or method '{func_name}'",
                )
            )

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        attr_name = node.attr
        if attr_name in self.policy.forbidden_attributes:
            self.findings.append(
                ASTFinding(
                    line=node.lineno,
                    column=node.col_offset,
                    rule="FORBIDDEN_ATTRIBUTE",
                    message=f"Access to forbidden introspection attribute '{attr_name}'",
                )
            )
        self.generic_visit(node)


def analyze_python_code(
    code_str: str,
    policy: SecurityPolicy,
    preset: str = "strict",
) -> tuple[list[ASTFinding], list[str]]:
    """
    Parses Python code and inspects AST against security policy.
    Returns (findings, list_of_imported_modules).
    """
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        finding = ASTFinding(
            line=e.lineno or 1,
            column=e.offset or 0,
            rule="SYNTAX_ERROR",
            message=f"Python syntax error in generated code: {e.msg}",
        )
        return [finding], []

    visitor = SecurityASTVisitor(policy, preset)
    visitor.visit(tree)
    return visitor.findings, visitor.imported_modules
