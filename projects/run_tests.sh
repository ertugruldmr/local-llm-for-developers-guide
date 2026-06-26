#!/usr/bin/env bash
# Run each package's tests from its own root (each package uses a top-level
# `backend` import, so they can't be collected together — see pytest.ini).
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="$HERE/.venv/bin/python"
[ -x "$PY" ] || PY="python3"

# Run from projects/ (so `common` is importable) with the package as the arg
# (pytest prepends the package root, so its top-level `backend` resolves).
# One process per package keeps same-named modules from colliding.
rc=0
cd "$HERE" || exit 1
for pkg in [0-9][0-9]-*/ extras/[0-9][0-9]-*/; do
  [ -d "${pkg}tests" ] || continue
  echo "=== ${pkg%/} ==="
  "$PY" -m pytest "${pkg%/}" -q || rc=1
done
exit $rc
