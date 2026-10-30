Feature: Include Bilingual Changes In Schedule Emails
  As a team contact
  I want the schedule email to explain changes in Dutch and English
  So that I understand the update before opening the attached PDFs

  Scenario: Send the same complete change report in both languages
    Given a valid report for "EHV HS1" with a collection-time change from "10:00" to "10:15"
      And the Dutch and English schedule PDFs are available
      And the team has configured email recipients
    When the update email is composed
    Then its body contains sections "Wijzigingen in het rijschema" and "Driving schedule changes"
      And both sections identify "EHV HS1" and the same baseline and current versions
      And both sections contain the old time "10:00" and new time "10:15" exactly once each
      And both sections precede the attachment reference
      And both PDFs are attached for the existing recipients

  Scenario: Include unavailable-baseline notices with the new PDFs
    Given a current schedule with no previous available version
      And its report contains the Dutch and English missing-baseline notices
      And both current PDFs are available
    When the update email is composed
    Then the body includes both missing-baseline notices
      And the email includes both PDFs
      And no invented match changes appear in the body

  Scenario: Include a long report without truncation
    Given a valid report for "EHV HS1" with 60 distinct change entries
      And both current PDFs are available
    When the update email is composed
    Then the Dutch section contains all 60 entries in the specified order
      And the English section contains the same 60 entries in the specified order
      And no change entry is replaced by an omitted-entry marker
