#!/usr/bin/env bash
# =============================================================================
# ContextSafe — deterministic pre-flight verifier (no LLM in the control path)
#
# Checks a Process Contract against the artifacts in this repository:
#   - status == certified
#   - next_recertification >= today
#   - SHA-256 of every SKILL.md == skill_hashes.<name>
#   - SHA-256 of the certified script == certified_script_hash
#   - owner != approved_by (warning only, PoC runs single-person)
#
# Usage:  ./scripts/verify.sh [process/<contract>.process.md]
# Exit:   0 = all gates pass, 1 = at least one gate failed
# =============================================================================
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONTRACT="${1:-$ROOT/process/tpch_q3.process.md}"
fail=0

sha256() {
    if command -v sha256sum >/dev/null 2>&1; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1
}

# Value of a top-level frontmatter key (first match, trailing comment stripped)
field() {
    awk -v key="$1" '$1 == key":" { sub(/^[^:]*:[ ]*/, ""); sub(/[ ]+#.*$/, ""); print; exit }' "$CONTRACT"
}

pass() { echo "PASS  $1"; }
fail() { echo "FAIL  $1"; fail=1; }

[ -f "$CONTRACT" ] || { echo "Contract not found: $CONTRACT"; exit 1; }
echo "Contract: ${CONTRACT#$ROOT/}"

# Gate: status
status="$(field status)"
[ "$status" = "certified" ] && pass "status = certified" || fail "status = $status"

# Gate: recertification date (ISO dates compare lexically)
next="$(field next_recertification)"
today="$(date +%F)"
if [ -n "$next" ] && [[ ! "$next" < "$today" ]]; then pass "next_recertification $next >= $today"
else fail "next_recertification '$next' < $today"; fi

# Gate: role separation (warning only)
owner="$(field owner | sed 's/ (.*//')"
approver="$(field approved_by | sed 's/ (.*//')"
[ "$owner" != "$approver" ] && pass "owner != approved_by" || echo "WARN  owner == approved_by ($owner)"

# Gate: skill hashes
while read -r name expected; do
    file="$ROOT/skills/$name/SKILL.md"
    if [ ! -f "$file" ]; then fail "$name: SKILL.md missing"; continue; fi
    actual="$(sha256 "$file")"
    [ "$actual" = "$expected" ] && pass "$name" || fail "$name  expected=$expected  actual=$actual"
done < <(awk '/^skill_hashes:/ { f = 1; next }
              f && /^  [a-z_]+:/ { sub(":", "", $1); print $1, $2; next }
              f { exit }' "$CONTRACT")

# Gate: certified script
script="$(field certified_script)"
expected="$(field certified_script_hash)"
if [ -f "$ROOT/sql/$script" ]; then
    actual="$(sha256 "$ROOT/sql/$script")"
    [ "$actual" = "$expected" ] && pass "$script" || fail "$script  expected=$expected  actual=$actual"
else
    fail "$script missing"
fi

[ "$fail" -eq 0 ] && echo "RESULT: all gates passed" || echo "RESULT: ABORT"
exit "$fail"
