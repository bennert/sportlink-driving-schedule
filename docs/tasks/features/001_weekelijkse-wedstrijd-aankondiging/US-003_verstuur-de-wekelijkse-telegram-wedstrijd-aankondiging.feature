Feature: Send the Weekly Telegram Match Announcement
  As a team contact
  I want to receive the weekly match announcement on Telegram
  So that I have the match and travel details without checking the PDF

  Scenario: Send the announcement even when the driving schedule is unchanged
    Given the Monday workflow has an announcement for a team
      And the team has configured Telegram chat destinations
      And the driving schedule content has not changed
    When the weekly notification step runs
    Then the Telegram Bot API accepts a message for each configured destination
      And the notification step runs independently of PDF generation

  Scenario: Report a rejected Telegram send request
    Given the Monday workflow has an announcement for a team
      And the Telegram Bot API rejects the send request
    When the weekly notification step runs
    Then the workflow reports the delivery as failed
      And the rejected message is not reported as successfully sent