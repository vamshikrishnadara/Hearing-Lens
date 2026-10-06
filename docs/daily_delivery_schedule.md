# Daily delivery schedule

Last status update: October 6, 2026 (Tuesday). This date records the snapshot;
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

## Current position and carryover - October 6

Today is Tuesday, October 6, in Week 4. Its planned work is due by Friday
October 9. Wednesday-Friday work is scheduled, not overdue. Do not say Week 4
is complete yet.

Monday's gap-calculation module is implemented, tested and pushed. The full
suite now passes 190 tests. October 6 added an independent spreadsheet formula
comparison of eight fictional gap rows, question detection and a blind 200-sentence
review with save/resume controls and a guarded evaluator. The spreadsheet commit
is pushed; the remaining changes await push approval. Human spreadsheet review and question labels remain
pending. Grouping/ranking/matching and the full-pipeline command are still scheduled.

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
| Tue Oct 6 | BUILT: eight-row spreadsheet formula comparison (pushed), question detection, 200-sentence blind review and evaluator; 190 tests pass. Human arithmetic check and labels pending; remaining pushes await approval. |
| Wed Oct 7 | Question grouping, frequency/subgroup-spread ranking, optional agency-response matching, and top three unanswered. |
| Thu Oct 8 | Chain modules into one command; validate complete outputs, missing-field behavior, question recall and false positives. |
| Fri Oct 9 | Close required failures, demonstrate Gate 2, update methodology/status and prepare the weekly public update. |

Human dependency before Friday: complete the spreadsheet hand-check and the
200-sentence review, resolve uncertain labels, then measure question performance.
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
