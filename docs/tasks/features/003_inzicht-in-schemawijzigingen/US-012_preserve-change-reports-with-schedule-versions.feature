Feature: Preserve Change Reports With Schedule Versions
  As a schedule maintainer
  I want the change report to remain attached to its schedule version
  So that email and regenerated PDFs explain the same version consistently

  Scenario: Keep a report available after previous files are removed and artifacts restored
    Given a changed schedule version "B" for "EHV HS1" compared with version "A"
      And its report contains one collection-time adjustment
    When the generation run removes version "A" and publishes its artifacts
      And the next run restores those artifacts
    Then the restored version "B" has the same collection-time adjustment and baseline reference
      And its source match identifiers remain available for the next comparison
      And consumers can read the report without reading version "A"

  Scenario: Preserve the report during an unchanged run
    Given current version "B" has a report describing changes since version "A"
      And the next calendar retrieval produces no relevant schedule differences
    When the next generation run completes
    Then version "B" retains its report describing changes since version "A"
      And its regenerated PDFs use that retained report
      And no schedule-update email is requested
      And the current run is recorded as having no schedule changes

  Scenario Outline: Reject unusable reports for a newly changed version
    Given a newly changed schedule version "B" for "EHV HS1"
      And its report is "<problem>"
    When email and PDF consumers attempt to use that report
    Then a report error identifies "EHV HS1" and version "B"
      And no update email for that version is sent
      And no PDF claiming no changes is published for that version

    Examples:
      | problem                  |
      | missing                  |
      | invalid JSON             |
      | unsupported schema       |
      | assigned to another team |
      | assigned to version A    |
