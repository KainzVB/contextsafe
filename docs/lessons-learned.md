# Lessons Learned: the 2026 outage

**Period:** 2026-06-15 → 2026-10-19 (17 scheduled runs, all aborted)
**Resolved:** 2026-10-25 (re-certification, contract v0.8.0)

## What happened

| Date | Event |
|------|-------|
| ≤ 2026-06-15 | The content of `skill_read_process_md` and `skill_send_html_email` changed without re-certification. Cause unknown. A later restore or iCloud re-download on 2026-07-05 (all files carry that date) erased any file-level trace. |
| 2026-06-15 | First pre-flight abort (SKILL-GATE 2). Status → `suspended`. Error log + admin email. |
| 2026-06-22 → 2026-09-14 | Same abort every Monday. From 2026-08-10 the error logs themselves recommend escalation. |
| 2026-09-27 | Obsidian connector replaced (archived plugin broke). 3 skills migrated and re-hashed. The drift is found during the migration and documented. Change package prepared. |
| 2026-09-28 → 2026-10-19 | Aborts now report 4 mismatching skills: the migrated files are not yet re-certified. |
| 2026-10-02 | Recertification date passes. The process is already suspended. |
| 2026-10-25 | Drift reviewed and new baseline approved. Re-certified. Run succeeds. |

## What worked

- **Fail-closed:** no run executed with uncertified instructions, 17 out of 17 times.
- **Evidence:** every abort produced a structured error log naming the gate, the skills and both hashes. The post-mortem was possible from these logs alone.
- **Self-diagnosis:** the error logs counted consecutive failures and escalated their wording.

## What did not work

1. **Escalation.** Alerts went to the same inbox as everything else for 18 weeks. A gate that blocks is only half a control; the other half is someone reacting.
2. **Recoverability.** The certified versions of the skills were not in version control: the backup had been failing since 2026-03-18. Drift was *detectable* but not *explainable*. The approver had to accept the current content as a new baseline.
3. **Supply chain.** An archived community MCP plugin was a single point of failure. It would have broken Step 1 even without the drift.
4. **Self-reporting.** The orchestrating LLM ran and reported the hash checks. This time the reports were accurate, but nothing proves that independently.
5. **Configuration drift in operations.** The configured narration model (Haiku) was never available, and the 2026-10-25 run executed on a Sunday. Neither stopped the pipeline.

## Changes made / planned

| Lesson | Action | Status |
|--------|--------|--------|
| Recoverability | Automated git backup every 10 min, including skills | ✅ since 2026-09-27 |
| Recoverability | Pin certified state to a git commit (ROADMAP E) | ⏳ |
| Escalation | Pause schedule + second channel after 2 consecutive aborts (R9) | ⏳ |
| Supply chain | Connector maintenance status in threat assessment (G); tool abstraction (H) | ⏳ |
| Self-reporting | Deterministic verifier `scripts/verify.sh`; deterministic orchestrator (I) | 🟡 verifier ✅, orchestrator ⏳ |
| Model drift | Enforce or flag the narration model (R11) | ⏳ |
