---
use_case_id: <DOMAIN-NAME-001>
use_case_name: <Short descriptive name>
version: 0.1.0
status: draft                     # draft | review | certified | suspended | deprecated
owner: <Name (Use-Case Owner)>
created: <YYYY-MM-DD>
last_modified: <YYYY-MM-DD>
approved_by:                      # set by the approver, must differ from owner
approved_date:                    # set only when status becomes certified
next_recertification:             # e.g. approved_date + 6 months
change_log:
  - date: <YYYY-MM-DD>
    author: <Name>
    change: "v0.1.0 — Initial draft"
db_connection_ref: <mcp-connector-name>
db_schema: public
db_access_mode: read_only         # read_only is required by gate 5
admin_recipients:
  - admin@example.com
skill_sequence:
  - skill_read_process_md
  - skill_execute_sql_postgres
  - skill_narrativize_result
  - skill_send_html_email
  - skill_log_run_to_obsidian
  - skill_error_log
certified_script: <script_name>.sql
certified_script_hash:            # 64-char SHA-256, entered by the approver
script_certification_date:
skill_hashes:                     # 64-char SHA-256 per SKILL.md, entered by the approver
  skill_read_process_md:
  skill_execute_sql_postgres:
  skill_narrativize_result:
  skill_send_html_email:
  skill_log_run_to_obsidian:
  skill_error_log:
skill_hashes_certified_date:
max_result_rows: 10
output_format: table              # table | csv | json
email_recipients:
  - business-recipient@example.com
email_subject_template: "[ContextSafe] <Use case> — {date}"
schedule_enabled: false
schedule_cron:                    # e.g. "5 8 * * 1"
---

# <Use case name>

## Business question
<One paragraph: what decision does this result support, for whom, how often?>

## Data structure
| Table | Description |
|-------|-------------|
| `<table>` | <purpose> |

## Business rules
- Filters: <…>
- Metric definitions: <single source of truth: the certified script must implement exactly these>
- Ordering / limit: <…>

## Expected result
| Column | Type | Description |
|--------|------|-------------|
| `<col>` | <type> | <meaning> |

## Notes for the agent
1. <Exact table names, type casts, known pitfalls>
