#!/usr/bin/env bash
# Seguridad (AGENTS.md): en app/ nada de eval/exec, shell, subprocess ni escribir a archivos.
added="$(git diff "$FACTORY_BASE" -- app | grep -E '^\+[^+]' || true)"
bad="$(grep -nE '(^|[^A-Za-z_.])(eval|exec|open)\(|subprocess|os\.system|os\.popen|\.write_text\(|\.write_bytes\(|FileHandler|pickle\.' <<<"$added" || true)"
if [ -n "$bad" ]; then
  echo "El cambio en app/ tiene código que AGENTS.md prohíbe (eval/exec, shell o archivos):"
  echo "$bad"
  exit 1
fi
echo "seguridad ok"
