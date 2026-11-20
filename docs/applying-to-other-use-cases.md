# Applying ContextSafe to other use cases

TPC-H Query 3 is only the reference. The pattern is a **lifecycle** that fits almost any recurring, data-driven task where a result has to be trustworthy, repeatable and explainable.

## The seven steps, generalised

| Step | Question to answer | Typical artifact |
|------|--------------------|------------------|
| 1. Explore | What data exists, and what does the question need? The LLM sees metadata only. | Schema notes, sample-free data dictionary |
| 2. Codify | Can the computation be expressed deterministically? | SQL, dbt model, Python script, notebook, API call, extraction template |
| 3. Contract | Who owns it, who approves it, who receives it, how often, which data access? | Process Contract |
| 4. Certify | Is exactly this version approved? | SHA-256 (later: signature) of artifact and agent instructions |
| 5. Execute | Are all gates green? Only then run, read-only, and return the result set only. | Gate checks, execution log |
| 6. Evidence | Can a third party reconstruct what ran, on which version, with which result? | Run log, error log, change log, versioned history |
| 7. Recertify | Is it still correct, still needed, still the approved version? | Expiry date, drift detection, diff review |

## Where the LLM adds value, and where it must not decide

| LLM at the edges ✅ | Deterministic core 🔒 |
|---------------------|-----------------------|
| Exploring schemas and documentation | Computing numbers |
| Drafting the artifact (for human review) | Choosing which artifact runs |
| Explaining and narrating results | Gate decisions, hashing, scheduling |
| Classifying unstructured input *before* a certified step | Writing back to operational systems |
| Preparing change packages and diff reports | Certifying or approving |

## Example mappings

| Domain | Certified artifact | Result set entering the context | LLM role |
|--------|--------------------|---------------------------------|----------|
| Sales / pipeline | SQL or semantic-layer query on CRM data | Pipeline KPIs by stage | Weekly narrative for the forecast call |
| Finance | Reconciliation workflow | Exceptions list | Explain exceptions, draft follow-ups |
| Supply chain | Reorder-point calculation | Items below threshold | Prioritised action summary |
| Compliance | Rule-based screening job | Flagged cases (IDs + reasons) | Case summaries for the reviewer |
| HR / people analytics | Aggregation with minimum group size | Aggregates only (k-anonymous) | Trend commentary |
| Document processing | Fixed extraction schema + validation | Validated fields | Classify document type before extraction |

## Platform equivalents

The core idea is to let the model choose from, or narrate, **pre-approved deterministic assets**. It exists natively on major data platforms:

| Platform | Equivalent |
|----------|-----------|
| Snowflake | Verified queries in semantic views, used by Cortex Agents |
| Databricks | Genie *trusted assets* (parameterised example SQL, Unity Catalog functions); responses are labelled when a trusted asset produced them |
| Workflow engines | Scheduled, versioned workflows with a single LLM step |

ContextSafe adds two things on top: **certifying the agent's own instructions** (skills) and a **human-readable contract with a lifecycle**.

## When *not* to use this pattern

- **Exploratory, one-off questions:** certification overhead exceeds the value. Use a governed semantic layer with ad-hoc querying instead.
- **Real-time or interactive use:** the gates and the human approval loop are built for scheduled or recurring work.
- **Simple scheduled reports without any LLM step:** a BI subscription is enough.
- **When the computation itself cannot be made deterministic:** for example, LLM-based judgement as the core result. Use evaluation and monitoring frameworks instead. Hashing the prompt does not make the output reproducible.

## Minimum viable adoption

1. One contract per use case (copy the template).
2. Hash the artifact and the agent instructions, and check them before every run with a deterministic script (`scripts/verify.sh`).
3. Read-only data access, result set only.
4. A run log and an error log for every execution.
5. A recertification date and someone who actually receives the alerts.
