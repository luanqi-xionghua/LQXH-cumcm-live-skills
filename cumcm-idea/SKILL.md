---
name: cumcm-idea
description: Explicitly invoked controller for a complete CUMCM or similar Chinese mathematical-modeling problem. Run a sentence-level problem audit first, then generate a coherent whole-paper modeling-idea framework from that audited interpretation, and deliver exactly one CUMCM_IDEA.md handoff document for a later cumcm-t2 conversation. Do not solve numerically, write the paper, freeze a model, or review a finished paper.
---

# CUMCM Idea Controller

Use this skill when the user explicitly invokes `$cumcm-idea` and supplies a complete mathematical-modeling contest problem. It combines two sequential protocols:

1. `bzd-problem-translator`: sentence-level semantic translation, hidden-condition discovery, dependency reconstruction, and omission audit;
2. `bzd-modeling-ideas`: whole-problem modeling backbone, candidate comparison, model-selection rationale, innovations, and validation planning.

This is a controller, not a blind concatenation. Phase 2 must consume the audited Phase-1 interpretation. Do not run both phases independently and merge contradictory reports afterward.

## Required input

Require the complete substantive problem:

- actual problem title and all numbered questions/subquestions;
- background, definitions, tables, figures, captions, notes, and appendices;
- attachment descriptions, data dictionaries, and required result-file specifications;
- actual attachment data when its structure or values materially affect model choice.

If a referenced page, attachment, field definition, or output template is missing, identify it. Do not claim complete coverage or recommend a data-dependent primary model whose feasibility cannot be assessed.

## Required references

Read all of the following completely before producing the report:

- [Phase-1 controller protocol](references/problem-translator-protocol.md)
- [Sentence interpretation rules](references/sentence-interpretation-rules.md)
- [Historical review signals](references/historical-review-signals.md)
- [Phase-2 controller protocol](references/modeling-ideas-protocol.md)
- [Integrated modeling patterns](references/integrated-modeling-patterns.md)
- [Strategy output standard](references/strategy-output-standard.md)
- [Combined output contract](references/cumcm-idea-output-contract.md)

The two imported controller protocols were originally standalone skills. When their standalone file-output rules conflict with this controller, the combined output contract controls: produce one final Markdown file only.

## Sequential workflow

### Phase 1: problem audit

Execute the problem-translator protocol first.

1. Locate the actual problem-title anchor and exclude only generic pre-title boilerplate.
2. Read the complete substantive problem before interpreting individual sentences.
3. Build stable source-unit IDs and a sentence-coverage ledger.
4. Preserve every number, unit, interval, direction, definition, information restriction, constraint, deliverable, and attachment requirement.
5. Separate prompt facts from ambiguity resolutions and newly introduced assumptions.
6. Build the per-question input-task-output table and the semantic cross-question dependency graph.
7. Audit source-unit coverage, numbered-question coverage, attachment coverage, ambiguity, and OCR uncertainty.

Do not propose detailed models during the sentence ledger. Model-family signals may be noted only when they clarify the mathematical meaning of the prompt.

### Phase-1 gate

Before Phase 2, verify:

- every substantive source unit appears exactly once in the ledger;
- every numbered question appears in the input-task-output table and semantic Mermaid graph;
- every required deliverable and attachment is represented;
- unresolved ambiguities and missing inputs are explicit;
- the graph contains real dependency labels rather than a decorative question-number chain.

If a missing or ambiguous input would materially change the model family, constraints, or requested output, set `HANDOFF_STATUS: BLOCKED_MISSING_INPUT`. Complete the auditable Phase-1 sections and the blocker section, but do not pretend Phase 2 is definitive. Conditional candidate branches are allowed only when their triggering assumptions are explicit.

### Phase 2: modeling ideas

After the Phase-1 gate, execute the modeling-ideas protocol using the ledger, term table, question interfaces, and dependency graph as authoritative inputs.

1. Reconstruct the whole-problem modeling backbone.
2. Establish shared objects, variables, parameters, units, time/coordinate conventions, preprocessing rules, constraints, objectives, and metrics.
3. For every numbered question, explain the task, known inputs, exact output, mathematical essence, and interfaces with other questions.
4. Compare genuinely distinct feasible candidates on the same target. When meaningful, include a recommended primary candidate, a usable baseline, and at most one conditional fallback.
5. Explain selection using data support, assumptions, interpretability, accuracy needs, implementation cost, validation, and downstream compatibility.
6. Design fair comparisons, sensitivity/uncertainty analysis, feasibility checks, and independent validation.
7. Propose only implementable innovations with a baseline, changed component, measurable comparison, risk, and fallback.
8. Audit the final route against every Phase-1 requirement and dependency.

If Phase 2 discovers that the Phase-1 interpretation is inconsistent, return to Phase 1, correct the ledger and affected interfaces, and repeat the gate before finalizing. Do not silently change the meaning of the prompt inside the modeling section.

## Output

Produce exactly one UTF-8 Markdown file following the combined output contract. Use the user's requested path; otherwise name it `CUMCM_IDEA.md` in the current task output directory or contest workspace.

The file must be self-contained for a later, separate conversation. Include source-file identity, attachment coverage, unresolved issues, and a clear handoff notice.

Set one of these statuses near the top:

- `HANDOFF_STATUS: IDEA-DRAFT-READY` — problem audit is complete enough for `cumcm-t2` to revalidate and continue;
- `HANDOFF_STATUS: CONDITIONAL` — useful routes exist, but named assumptions or missing data can change selection;
- `HANDOFF_STATUS: BLOCKED_MISSING_INPUT` — a reliable modeling route cannot yet be selected.

End with a `给 cumcm-t2 的交接说明` stating that:

- this document is an idea draft, not `PROBLEM_CONTRACT.md` or `MODELING_REPORT.md`;
- the original problem, attachments, and current official rules remain authoritative;
- `cumcm-t2` must revalidate the prompt, run risk probes, obtain the required method decision, and freeze contracts before coding;
- expected behaviors, hypothetical examples, and candidate comparisons in this file are not numerical results;
- no value from this document may enter the paper as an experimental result without actual computation and verification.

In chat, return only a concise completion note and a clickable link when file creation is available. Do not paste the full report.

## Boundaries

- Do not write solution code, execute the full numerical solution, fabricate coefficients/results/accuracy, or claim an optimum.
- Do not create a paper, abstract, score, award estimate, or review report.
- Do not mark `CONTRACT-OK`, `MODEL-FROZEN`, `RESULTS-FROZEN`, or any `cumcm-t2` gate as passed.
- Do not invoke `cumcm-review`; that belongs after a paper package exists.
- Do not create separate translator and modeling-ideas reports. The one combined Markdown file is the handoff artifact.
