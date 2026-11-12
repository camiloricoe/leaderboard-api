#!/usr/bin/env bash
# Funciones de menos de 30 líneas en app/ (AGENTS.md).
python3 - <<'PY'
import ast, pathlib, sys
bad = []
for f in sorted(pathlib.Path("app").rglob("*.py")):
    for n in ast.walk(ast.parse(f.read_text(), str(f))):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            size = n.end_lineno - n.lineno + 1
            if size >= 30:
                bad.append(f"{f}:{n.lineno} {n.name}() tiene {size} líneas")
if bad:
    print("AGENTS.md pide funciones de menos de 30 líneas:")
    print("\n".join(bad))
    sys.exit(1)
print("funciones ok")
PY
