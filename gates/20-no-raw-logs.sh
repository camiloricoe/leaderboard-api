#!/usr/bin/env bash
# No raw user data on disk: the change may not touch logs/ nor make app code write files or keep raw request bodies.
set -u
base="${FACTORY_BASE:-HEAD}"
changed="${FACTORY_CHANGED:-}"

if grep -qE '(^|/)logs/' <<<"$changed"; then
  echo "The change writes under logs/. Request data never goes to a (public) file."
  exit 1
fi

added="$(git diff "$base" -- app | grep -E '^\+[^+]' || true)"
bad="$(grep -nE "logs/|open\(|\.write\(|write_text|write_bytes|FileHandler|request\.body|await request\.(body|json)|Request\b" <<<"$added" || true)"
if [ -n "$bad" ]; then
  echo "The change makes app/ write files or read raw request bodies (user data):"
  echo "$bad"
  exit 1
fi
exit 0
