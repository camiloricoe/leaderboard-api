#!/usr/bin/env bash
# Todo cambio en app/ llega con su test en tests/ (AGENTS.md).
if grep -q '^app/' <<<"$FACTORY_CHANGED" && ! grep -q '^tests/' <<<"$FACTORY_CHANGED"; then
  echo "Cambió app/ pero no tests/: cada endpoint necesita su test (AGENTS.md)."
  exit 1
fi
echo "tests ok"
