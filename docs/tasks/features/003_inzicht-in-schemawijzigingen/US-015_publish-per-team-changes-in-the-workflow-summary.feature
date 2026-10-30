Feature: Publish Per-Team Changes In The Workflow Summary
  As a schedule maintainer
  I want a per-team change overview in the workflow summary
  So that I can inspect changes without searching raw Markdown diffs

  Scenario: Separate changed and unchanged teams in a single run
    Given "EHV HS1" has two relevant changes in the current run
      And "EHV DS1" has no relevant changes in the current run
      And "EHV DS1" retains a report from its previous version update
    When the workflow comparison summary is published
    Then "EHV HS1" shows both current changes in Dutch and English with its version references
      And "EHV DS1" shows "Geen schemawijzigingen" and "No schedule changes"
      And the old report for "EHV DS1" is not presented as new changes
      And no email addresses or credentials appear in the comparison summary

  Scenario: Keep comparison results visible after email delivery fails
    Given "EHV HS1" has a valid report with 60 current change entries
      And the comparison summary has been published
    When the subsequent email delivery fails
    Then all 60 entries remain visible in Dutch and English in the workflow summary
      And the summary makes no claim of successful email delivery

  Scenario: Display a comparison-unavailable state without claiming no changes
    Given "EHV HS3" has no previous available schedule
      And its current schedule was generated successfully
    When the workflow comparison summary is published
    Then "EHV HS3" shows "Geen vorige versie beschikbaar; wijzigingen konden niet worden bepaald"
      And "EHV HS3" shows "No previous version available; changes could not be determined"
      And "EHV HS3" is not labelled as having no schedule changes
