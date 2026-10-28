Feature: Send the Weekly WhatsApp Match Announcement
  As a team contact
  I want to receive the weekly match announcement on WhatsApp
  So that I have the match and travel details without checking the PDF

  Scenario: Send the announcement even when the driving schedule is unchanged
    Given the Monday workflow has an announcement for a team
      And the team has configured opted-in WhatsApp recipients
      And the driving schedule content has not changed
    When the weekly notification step runs
    Then the WhatsApp provider receives the announcement for each configured recipient
      And the notification step runs independently of PDF generation

  Scenario: Report a rejected WhatsApp delivery
    Given the Monday workflow has an announcement for a team
      And the WhatsApp provider rejects the send request
    When the weekly notification step runs
    Then the workflow reports the delivery as failed
      And the rejected message is not reported as successfully sent