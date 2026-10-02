> Updated October 2: the fellow reports that Benjamin does not require formal
> gate approval meetings for now. References below describe the original review
> milestones; they do not block continued development. Quality benchmarks, real
> human validation, and genuine pilot participation still apply. Current status:
> [delivery checklist](gate_status.md).

# Daily delivery schedule - updated October 2, 2026

## Planning basis

Source: the official Hearing Lens Project Brief, Sections 6, 13, and 15.
September 14 is the working start date supplied by the fellow; the brief leaves
formal kickoff agreement to Benjamin. Dates below use that assumption. Work is
planned Monday-Friday. Weekly calendar ranges end Sunday, but delivery should
be ready for the Friday check-in; no weekend work is assumed.

Target completion: end of Week 7, November 1, with planned handoff by Friday,
October 30. Week 8 is a buffer for slippage/fixes, not planned new features.
The reported waiver of formal gate approvals changes the meeting process; the
weekly deliverables and quality requirements remain applicable.

## Operating rules

1. Start each day by naming the weekly deliverable, unmet acceptance criteria,
   and the concrete result that today's work must produce.
2. Prioritize missing required features over optional tuning or cosmetic changes.
   A daily task can cover multiple components when the weekly outcome requires it.
3. Check progress midweek and reserve time for integration, measured validation,
   documentation, and the live demonstration. Prepare required human-review
   inputs early rather than leaving them for the deadline.
4. If a deliverable is at risk, disclose it immediately with the exact missing
   work and dependency. Do not promise completion without evidence, silently
   move work into another week, or extend the agreed deadline unilaterally.
5. When required work and validation finish early, use remaining time for bugs,
   clarity, robustness, and review within the approved scope. Stretch features
   remain frozen until core deliverables are complete. Formal gate meetings are
   not a prerequisite under Benjamin's reported instruction.
6. Organize meaningful commits around changes, not a daily quota. Ask the fellow
   before each push. Personal daily evidence is separate from product exports
   and never substitutes for a project deliverable.
7. End each day with completed/remaining/blocked status against the weekly target.
   Record implementation, verification, and supervisor approval separately.

## Current recovery window: Week 3, September 28-October 4

**Planning snapshot before the October 1 catch-up implementation: at risk.** Week 3 requires sentiment, emotion, timeline, and
60 genuinely hand-labeled comments (20 per corpus), plus the completed theme
foundation demonstrated on all three corpora. There is no affect module or
validation directory yet. The federal corpus and parts of Week 2 remain missing.
The following are catch-up targets, not guaranteed two-day completion. For the
latest implemented features and remaining blockers, use [gate status](gate_status.md).

| Day | Required outcome and priority | Completion evidence |
| --- | --- | --- |
| Thu Oct 1 | Close the main theme-engine implementation gaps (BERTopic routing, required keyword/quote behavior); prepare the federal development corpus and the three-corpus validation inputs; implement sentiment/emotion inference and theme aggregation. Prepare the 60-comment sheet as soon as inputs exist so human labeling can begin. | Working library runs, failure handling, tests, source provenance, blank human-label sheet and labeling instructions; explicit list of remaining theme criteria. |
| Fri Oct 2 | Integrate timeline by date/hearing and its missing-date behavior; run the three-corpus checks, compare genuine human labels when available, record performance and limitations, and prepare Gate 1 demonstration. | Affect/timeline tests, three-corpus outputs, validation table, methodology draft, timed runs, live-demo checklist with actual pass/fail/pending states. |

The breadth of the backlog makes this window high risk. Do not call Gate 1
complete if theme benchmarks, corpus preparation, human labels, or the demo are
missing. Ask the fellow to confirm Gate 0 status and Benjamin's Gate 1 meeting
and labeling availability. Prepare a factual recovery/status update if needed;
do not send it without authorization. Any scope or schedule adjustment must be
agreed with Benjamin. Finishing code alone does not pass a gate.

## Week 4: October 5-11 - gaps, questions, complete pipeline

Dependent on analytical-core readiness. If validation is incomplete, show the conflict explicitly
rather than treating these dates as evidence that the next phase has begun.

| Day | Planned outcome |
| --- | --- |
| Mon Oct 5 | Representation calculations: supplied reference shares, percentage-point gaps, ratios, and suppression below 10 rows. |
| Tue Oct 6 | Validate gaps against a hand calculation; implement question detection and prepare the 200-sentence human review sample. |
| Wed Oct 7 | Question grouping, frequency/subgroup-spread ranking, optional agency-response matching, and top three unanswered. |
| Thu Oct 8 | Chain modules into one command; validate complete outputs, missing-field behavior, question recall and false positives. |
| Fri Oct 9 | Close required failures, demonstrate Gate 2, update methodology/status and prepare the weekly public update. |

Exit: exact gap hand-check; question recall at least 80% and false positives
below 10%; reviewed top-three questions; all analytical output types from one
command. Confirm two pilot partners with ChiEAC by the end of this week, as the
brief's risk mitigation requests, and arrange Week 7 dates early.

## Week 5: October 12-18 - dashboard and deployment

| Day | Planned outcome |
| --- | --- |
| Mon Oct 12 | Connect upload/mapping to analysis; Themes panel and quote-review controls. |
| Tue Oct 13 | Sentiment/emotion and Timeline panels with appropriate empty states. |
| Wed Oct 14 | Representation and Questions panels, labeled CSV download, and full-flow error handling. |
| Thu Oct 15 | Deploy the complete app; check memory, model reuse, privacy, all three corpora, and the 2,000-row performance target. |
| Fri Oct 16 | Test with someone outside the project, fix blockers, verify the public URL and prepare the weekly update. |

Exit: five panels and labeled CSV at a public URL, clear missing-field states,
first-time use in under five minutes, and a 2,000-row run under three minutes.
User testing and hosting permissions must be arranged before the relevant day.

## Week 6: October 19-25 - brief, methodology, pilot readiness

| Day | Planned outcome |
| --- | --- |
| Mon Oct 19 | Build the one-page community DOCX brief from actual analytical outputs. |
| Tue Oct 20 | PDF generation and downloads; check rendering, 11-point text, one-page layout, and generation time. |
| Wed Oct 21 | Complete the methodology, validation table, limitations, help text, and local setup instructions. |
| Thu Oct 22 | Test interpretation with two non-technical readers; fix clarity problems and confirm pilot data arrangements. |
| Fri Oct 23 | Demonstrate upload-to-brief flow for Gate 3, close blockers, finalize pilot plan and weekly update. |

Exit: brief in both formats in under 15 seconds, reader understanding checks,
models/validation/limitations published, two named pilot partners and dates,
and pilot readiness. Personal work-evidence PDFs are not the community brief.

## Week 7: October 26-November 1 - pilots, launch, handoff

Dependent on pilot readiness; pilot dates require partner agreement.

| Day | Planned outcome |
| --- | --- |
| Mon Oct 26 | Run first pilot; record findings and fix critical failures. |
| Tue Oct 27 | Run second pilot; address critical failures and verify fixes against both datasets. |
| Wed Oct 28 | Complete privacy/accessibility/performance checks and plain-language limitations; draft facilitator runbook. |
| Thu Oct 29 | Finish runbook, record the 3-5 minute demo, and prepare the two-page final report and release checklist. |
| Fri Oct 30 | Demonstrate Gate 4, resolve remaining critical issues, confirm readiness, publish/tag v1.0 and complete handoff. |

Exit: every Section 13 acceptance criterion demonstrated, both pilots complete,
no open critical bugs, runbook/video/final report delivered, and release readiness.
Do not mark launch complete merely because this date has arrived.

## Review and communication dependencies

A gate review is a live milestone demonstration with Benjamin. He checks the
listed benchmarks and approves progression; it is separate from permission to
push a commit. Target gates: Gate 0 end Week 1, Gate 1 end Week 3, Gate 2 end
Week 4, Gate 3 end Week 6, Gate 4 end Week 7. The brief specifies a regular
30-minute check-in; gate reviews may take 45 minutes and replace that week's call.
Approval status is currently unverified, not assumed refused or granted.

Prepare the weekly written status and required LinkedIn post with a synthetic
visual and required tags. Publish/send only with explicit authorization; verify
actual prior publication rather than counting drafts as posts. The brief calls
for weekly posts in Weeks 1-8 plus the launch post. Week 8 remains buffer only.
