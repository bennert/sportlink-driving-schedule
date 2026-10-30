# Feature Specification 003: Inzicht in schemawijzigingen

**Date:** 2026-10-30
**Status:** Draft
**Ideation:** [003: Inzicht in schemawijzigingen bij een nieuwe PDF](../ideation/003_inzicht-in-schemawijzigingen.md)
**Stories:** US-009 through US-015
**Feature Files:**

- [US-009_compare-schedule-versions-per-team.feature](features/003_inzicht-in-schemawijzigingen/US-009_compare-schedule-versions-per-team.feature)
- [US-010_exclude-costs-and-technical-route-changes.feature](features/003_inzicht-in-schemawijzigingen/US-010_exclude-costs-and-technical-route-changes.feature)
- [US-011_explain-the-schedule-comparison-baseline.feature](features/003_inzicht-in-schemawijzigingen/US-011_explain-the-schedule-comparison-baseline.feature)
- [US-012_preserve-change-reports-with-schedule-versions.feature](features/003_inzicht-in-schemawijzigingen/US-012_preserve-change-reports-with-schedule-versions.feature)
- [US-013_include-bilingual-changes-in-schedule-emails.feature](features/003_inzicht-in-schemawijzigingen/US-013_include-bilingual-changes-in-schedule-emails.feature)
- [US-014_include-localized-changes-in-schedule-pdfs.feature](features/003_inzicht-in-schemawijzigingen/US-014_include-localized-changes-in-schedule-pdfs.feature)
- [US-015_publish-per-team-changes-in-the-workflow-summary.feature](features/003_inzicht-in-schemawijzigingen/US-015_publish-per-team-changes-in-the-workflow-summary.feature)

## Context

Team contacts receive updated driving schedule PDFs without an explanation of what changed. A technical Markdown diff exists in workflow logs, but recipients must compare documents themselves. This specification adds one shared, structured change report per team and schedule version.

The requester explicitly selected email, workflow summary, and PDF as delivery surfaces, with Dutch and English text. Emails contain both languages; each PDF contains its own language. The workflow summary contains both languages. PDF inclusion extends the MVP suggested by Ideation 003.

## Scope And Rules

- Compare the new schedule with the previous available schedule for the same team, not with a claimed last-delivered email. Identify both versions using the source filename and a content digest; date alone is insufficient for multiple updates on one day.
- Match by a stable source match identifier unique within both versions when available. Preserve source identifiers alongside schedule data for future comparisons. For legacy Markdown without identifiers, match only by an exact date and match description pair unique within both versions. Do not use fuzzy matching. Unchanged rows are not reported as changes.
- Report changed date, weekday, match description, collection time, start time, end time, and location name using explicit old and new values. Report base location and warming-up time changes separately from match changes.
- An unmatched old row is 'Vervallen uit het schema' / 'Removed from the schedule', not 'Afgelast' / 'Cancelled'. An unmatched new row is 'Toegevoegd' / 'Added'. Preserve duplicate row counts; do not silently merge matches.
- Ignore travel costs, cost per kilometre, existing distance/duration metric values, and map URL changes. A different location name remains relevant. Preserve the existing treatment of legacy table-schema migrations; this feature does not redefine which document migrations trigger regeneration.
- Account for other document changes already considered relevant by the existing check, such as a changed logo reference, as 'Documentinformatie gewijzigd' / 'Document information changed', without inventing match changes. Use structural comparison rather than translated display text to avoid reporting the same match twice for the two languages.
- Display dates as DD-MM-YYYY and times as HH:MM in Europe/Amsterdam local time. List entries by match date, then match description, then change category; use the old date for removals and the new date for additions and modifications. Include each changed field once.
- Missing or unreadable previous versions are not empty schedules and do not prove first publication. Display an explicit unavailable-comparison notice and continue generating the current schedule; do not fabricate added or removed matches. A source-calendar retrieval failure remains a generation error, not an empty calendar.
- Retain the report belonging to the current schedule version across runs without relevant changes. A new run without relevant changes sends no update email and reports 'Geen schemawijzigingen' / 'No schedule changes' in the workflow summary, even though its PDFs retain the explanation from their last version change.
- Do not silently truncate reports. Emails, PDFs, and workflow summaries include all entries. Long PDF reports paginate without clipping. Missing or invalid report data must produce a visible team-specific error rather than a misleading successful update email or a PDF claiming no changes.
- Out of scope: visual highlighting of individual table cells, PDF-byte comparison, Telegram changes, notification retries, and history of successfully delivered versions. The existing full schedule table and costs remain visible in each PDF.

## User Stories

### US-009 Compare Schedule Versions Per Team

```text
AS A team contact
I WANT to see which matches and schedule settings changed
SO THAT I can identify the practical differences without comparing entire documents
```

**Complexity:** L
**Feature File:** [US-009_compare-schedule-versions-per-team.feature](features/003_inzicht-in-schemawijzigingen/US-009_compare-schedule-versions-per-team.feature)
**Acceptance Focus:**

- Report additions, removals, and old/new values for reliably matched rows and schedule settings.
- Use conservative matching for legacy and duplicate rows, preserving their counts.
- Separate non-match document changes from match changes.

**Dependencies:** Existing schedule generation and Markdown comparison; no dependency on another new story.
**Notes:** Inspect Sportlink identifiers before implementation. Identifier availability is not assumed; the exact unique date/description fallback defines implementable legacy behavior. Date or description changes without a stable identifier become removal plus addition. Compare before deleting old files. Use structured calendar data and a tested parser for historical tables, not console diffs.

### US-010 Exclude Costs And Technical Route Changes

```text
AS A team contact
I WANT cost and technical route differences excluded from change notifications
SO THAT I only receive explanations of relevant schedule changes
```

**Complexity:** S
**Feature File:** [US-010_exclude-costs-and-technical-route-changes.feature](features/003_inzicht-in-schemawijzigingen/US-010_exclude-costs-and-technical-route-changes.feature)
**Acceptance Focus:**

- Ignored-only differences create no schedule-update email or change entry.
- Mixed differences report only the relevant changes, including actual location-name changes.

**Dependencies:** US-009.
**Notes:** Reuse `strip_travel_metrics` semantics for both language versions. Do not remove displayed cost information from schedules. PDF regeneration for publication is distinct from an update notification.

### US-011 Explain The Schedule Comparison Baseline

```text
AS A team contact
I WANT to know which previous version was used for the change report
SO THAT I do not mistake an unavailable comparison for a first publication
```

**Complexity:** M
**Feature File:** [US-011_explain-the-schedule-comparison-baseline.feature](features/003_inzicht-in-schemawijzigingen/US-011_explain-the-schedule-comparison-baseline.feature)
**Acceptance Focus:**

- Valid comparisons identify the previous available and current versions without claiming delivery.
- Missing and unreadable baselines show distinct, explicit notices without fabricated match changes.

**Dependencies:** US-009.
**Notes:** Compare valid historical Markdown even without stored source identifiers. Missing identifier metadata alone does not make a readable baseline unavailable. Use 'Geen vorige versie beschikbaar; wijzigingen konden niet worden bepaald' / 'No previous version available; changes could not be determined' for missing baselines. Use 'Vorige versie onleesbaar; wijzigingen konden niet worden bepaald' / 'Previous version unreadable; changes could not be determined' for invalid baselines. Do not label any MVP run 'Eerste schema' / 'First schedule' without independent publication evidence.

### US-012 Preserve Change Reports With Schedule Versions

```text
AS A schedule maintainer
I WANT the change report to remain attached to its schedule version
SO THAT email and regenerated PDFs explain the same version consistently
```

**Complexity:** M
**Feature File:** [US-012_preserve-change-reports-with-schedule-versions.feature](features/003_inzicht-in-schemawijzigingen/US-012_preserve-change-reports-with-schedule-versions.feature)
**Acceptance Focus:**

- Reports survive removal of older files and restoration in the next workflow run.
- Unchanged runs preserve the current version's report without sending an update.
- Missing, invalid, wrong-team, and wrong-version reports cause explicit errors in consumers.

**Dependencies:** US-009, US-010, US-011.
**Notes:** Store a versioned JSON sidecar per team, for example `docs/schedule_changes_<team_id>.json`, including schema version, team ID, current and baseline version references, comparison status, and language-neutral entries. Preserve source match identifiers in a separate snapshot or a clearly separate section. Persist only the latest per-team state through workflow artifacts; store no credentials or recipient addresses. Reference canonical source data with a digest that excludes any embedded report to prevent self-generated change loops. This is a proposed format, not existing functionality. Legacy schedules without sidecars require a visible 'Wijzigingsoverzicht niet beschikbaar' / 'Change report unavailable' migration notice, not fabricated historical changes; a newly changed version must have a valid report before delivery.

### US-013 Include Bilingual Changes In Schedule Emails

```text
AS A team contact
I WANT the schedule email to explain changes in Dutch and English
SO THAT I understand the update before opening the attached PDFs
```

**Complexity:** M
**Feature File:** [US-013_include-bilingual-changes-in-schedule-emails.feature](features/003_inzicht-in-schemawijzigingen/US-013_include-bilingual-changes-in-schedule-emails.feature)
**Acceptance Focus:**

- Place complete Dutch and English reports before the attachment reference.
- Include team identity and comparison version references, including unavailable-baseline notices.
- Preserve existing recipients and PDF attachments without exposing ignored differences.

**Dependencies:** US-012.
**Notes:** Use 'Wijzigingen in het rijschema' and 'Driving schedule changes' as section headings. Both translations render the same entries; do not calculate changes twice. A report failure must not result in sending the generic old email as a fallback.

### US-014 Include Localized Changes In Schedule PDFs

```text
AS A team contact
I WANT the PDF to include a change report in the document language
SO THAT the explanation stays available when the PDF is forwarded or printed
```

**Complexity:** M
**Feature File:** [US-014_include-localized-changes-in-schedule-pdfs.feature](features/003_inzicht-in-schemawijzigingen/US-014_include-localized-changes-in-schedule-pdfs.feature)
**Acceptance Focus:**

- Each PDF includes the matching language, team identity, baseline, and complete change report.
- Put the report after the full schedule table, with a page break before the report.
- Long reports paginate without losing text, overlap, or changes to the complete schedule table.

**Dependencies:** US-012.
**Notes:** Retain existing landscape format and schedule layout. Include missing/unreadable-baseline notices instead of a fabricated comparison. Verify generated PDFs through text extraction and rendered-page inspection. Forwarding or rerendering a version must not change its report merely because another run occurred.

### US-015 Publish Per-Team Changes In The Workflow Summary

```text
AS A schedule maintainer
I WANT a per-team change overview in the workflow summary
SO THAT I can inspect changes without searching raw Markdown diffs
```

**Complexity:** M
**Feature File:** [US-015_publish-per-team-changes-in-the-workflow-summary.feature](features/003_inzicht-in-schemawijzigingen/US-015_publish-per-team-changes-in-the-workflow-summary.feature)
**Acceptance Focus:**

- Show changed, unchanged, and comparison-unavailable states separately per team.
- Present all current-run changes in Dutch and English using the same report as email and PDF.
- A later delivery failure does not hide a computed comparison or turn it into a delivery-success claim.

**Dependencies:** US-012; existing workflow reporting. Independent of Telegram delivery reporting in US-008.
**Notes:** Write comparison results to `GITHUB_STEP_SUMMARY` before delivery. Do not replay a retained historical report as a new change on an unchanged run. Escape source-provided text for Markdown/HTML rendering. Do not include email addresses or secret configuration in the comparison summary.

## Verification And Next Steps

- The `.feature` files define acceptance scenarios; generation of these files does not mean step definitions or application behavior have been implemented.
- Implement comparison and report persistence first, then the three output surfaces. Add tests beside existing schedule-content tests and reuse the repository's existing test framework.
- Include restored-artifact tests and PDF pagination/rendering checks; do not exercise live email, Sportlink, or Google Maps services during automated acceptance checks.
- Start implementation with `/coder` after reviewing this draft. No application code is changed by this specification.
