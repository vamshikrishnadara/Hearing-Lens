# Daily delivery schedule

Last status update: October 9, 2026 (Friday). This date records the snapshot;
recalculate the current week from the live session date at every new work session.

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

## Current position and carryover - October 9

Friday's implemented work is fictional-only workflow validation and preparation
of blank human-review materials. Five scenarios passed twice, with matching JSON
and verified exports. The fictional 1,000-row benchmark measured 19.96/7.48 seconds;
188 targeted tests passed. The eight-group workbook matches the pipeline in software.
Both October 8 commits are pushed at `e38f416`; today's five commits require separate
push approvals. This update supersedes the October 8 snapshot and Friday plan below.

Do not describe Week 4 as fully validated: the 200 question labels, independent
top-three choices and arithmetic hand-check remain pending, along with earlier
theme/affect review. The new packet is fictional and contains repeated wording;
it does not establish real-submission accuracy or close earlier performance findings.
No further tests on other datasets are scheduled under the current data preference.
Pilot-partner confirmation and actual publication have not been verified.

Week 5 begins Monday October 12 with upload-to-analysis and dashboard integration.
Carryover validation stays explicitly pending while implementation continues.
The planned working handoff remains Friday October 30; later scheduled work is
not yet overdue.

## Historical position and carryover - October 8

Today is Thursday, October 8, in Week 4, with the weekly target on Friday
October 9. All four October 7 commits are pushed and verified at `8770837`.
The full command-line workflow is now built and tested locally: 243 tests pass,
all three corpora pass structural checks, and repeated JSON results are identical.
The expanded CFPB workflow repeats in 34.11 seconds, above the 30-second target;
record this performance refinement alongside Friday's validation work. Today's
work has two commits: `1fe9ce5` is pushed, and the combined remaining commit
awaits approval.

The eight-row spreadsheet check, 200 question labels and independent top-three
review still require genuine human input. No question recall/false-positive rate
or human acceptance can be claimed yet. Full-pipeline integration is implemented;
these validation requirements remain open.

Keep earlier carryover separate: human theme/quote review; 60 sentiment/emotion
labels and the resulting agreement/remediation; an undecided license; and
unverified publication of required updates. No formal gate approval is needed
to continue under Benjamin's reported instruction. Do not mark these items
complete because the calendar advances, and do not treat future Week 4 tasks as
those earlier outstanding items.

## Week 4: October 5-11 - gaps, questions, complete pipeline

October 5: Week 4 development has begun at the fellow's request. Earlier human
theme/affect validation is still pending and must remain on the closeout list.
The gap module and question detection are implemented and numerically/behaviorally
checked. The spreadsheet is prepared, not human-reviewed. The remaining Week 4
tasks and human validation are not complete.

| Day | Planned outcome |
| --- | --- |
| Mon Oct 5 | DONE: representation calculations, supplied-reference validation, gaps/ratios, and small-group suppression; tested and pushed. |
| Tue Oct 6 | BUILT AND PUSHED: eight-row spreadsheet formula comparison, question detection, 200-sentence blind review and evaluator; 190 tests passed. Human arithmetic check and labels pending. |
| Wed Oct 7 | BUILT AND PUSHED: grouping, protected ranking, supplied-response matching and top-three priorities; 222 tests and three-corpus checks pass. Human top-three review pending. |
| Thu Oct 8 | BUILT LOCALLY: one command for all modules, protected local exports and missing-field behavior; 243 tests and repeated three-corpus structural checks pass. CFPB repeat 34.11s exceeds 30s target; human question accuracy remains unmeasured. First commit pushed; combined second commit awaits approval. |
| Fri Oct 9 | Address CFPB full-run performance, complete genuine human validation, close required failures, demonstrate the full pipeline, update methodology/status and prepare the weekly public update. |

Human dependency before Friday: complete the spreadsheet hand-check and the
200-sentence review, resolve uncertain labels, then measure question performance.
Also supply independent top-three picks and explain differences if needed. These
human checks are now the main dependency for Friday's validation deadline.
The earlier 60-comment affect/theme review is separate carryover. Automated work
cannot close these human requirements.

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

The original brief uses gates as milestone demonstrations: scope/schema at the
end of Week 1, analytical core at the end of Week 3, full pipeline at the end of
Week 4, pilot readiness at the end of Week 6, and launch at the end of Week 7.
Benjamin's formal gate approvals are not required to proceed, per the fellow's
reported instruction. Genuine validation, user testing and pilot participation
are still required. GitHub push approval is a separate user preference.

Weekly reports cover work actually completed Monday-Friday. A report sent at
the start of a new week normally summarizes the previous completed workweek;
label any current-week work separately. On Monday October 5, the prior report
period is September 28-October 2 (Week 3), while Week 4 is October 5-9 and has
just begun. Never describe scheduled future work as completed or overdue.

Prepare written updates and required public-post drafts locally. Send or publish
only with explicit authorization; drafts are not evidence of publication.
Keep personal evidence and status links out of the README and repository description.

## Date handling at every work session

Use the latest client/environment date in America/New_York; never carry an old
message date forward. Week number = floor((current date - 2026-09-14) / 7) + 1.
Week calendar ranges are Monday-Sunday; execution/report periods are Monday-Friday.
A date before kickoff is pre-project, and a date after November 8 is beyond the
planned buffer, not a reason to silently renumber the schedule.

At session start, determine the date/week/day, consult verified completion status,
and select the next unfinished task due in that week. Carry earlier uncompleted
requirements on a separate list. During the week, allow time for testing and
integration; if ahead, refine that week's work. If the deadline is at risk, state
the specific dependency promptly without treating not-yet-due work as late.
This is session-by-session planning, not an unattended daily automation.
