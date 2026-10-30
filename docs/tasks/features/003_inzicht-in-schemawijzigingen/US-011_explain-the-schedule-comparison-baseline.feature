Feature: Explain The Schedule Comparison Baseline
  As a team contact
  I want to know which previous version was used for the change report
  So that I do not mistake an unavailable comparison for a first publication

  Scenario: Identify two available versions without claiming successful delivery
    Given a readable previous schedule and a changed current schedule for "EHV HS1"
      And both versions were generated on the same calendar date
      And no successful email delivery history exists
    When the change report is created
    Then it identifies the previous and current versions using their filenames and distinct content digests
      And it describes the baseline as the previous available schedule
      And it makes no claim that the baseline was received by the team

  Scenario: Explain a missing previous version
    Given no previous schedule is available for "EHV HS1"
    When its current schedule is generated
    Then the comparison status is unavailable
      And the Dutch notice is "Geen vorige versie beschikbaar; wijzigingen konden niet worden bepaald"
      And the English notice is "No previous version available; changes could not be determined"
      And no added or removed matches are inferred
      And the current schedule remains available for PDF generation
      And the report does not claim this is the first publication

  Scenario: Explain an unreadable previous version
    Given the previous schedule for "EHV HS1" cannot be parsed as a schedule
      And the current calendar was retrieved successfully
    When its current schedule is generated
    Then the comparison status is unavailable
      And the Dutch notice is "Vorige versie onleesbaar; wijzigingen konden niet worden bepaald"
      And the English notice is "Previous version unreadable; changes could not be determined"
      And no added or removed matches are inferred
      And the current schedule remains available for PDF generation
