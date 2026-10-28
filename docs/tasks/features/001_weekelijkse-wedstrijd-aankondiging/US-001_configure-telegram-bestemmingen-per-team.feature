Feature: Configure Telegram Destinations Per Team
  As a team coordinator
  I want to configure Telegram chat destinations for each team
  So that weekly announcements reach the right team contacts

  Scenario: Use configured Telegram destinations for their assigned team
    Given a team has valid Telegram chat destinations configured
      And private recipients have started the bot or the bot has been added to the configured group
    When the weekly announcement is prepared for that team
    Then only those destinations are eligible to receive that team's announcement
      And destinations configured for another team are excluded

  Scenario: Do not send to a team with invalid Telegram destination configuration
    Given a team has a missing or invalid Telegram chat destination
    When the weekly announcement is prepared for that team
    Then no Telegram message is sent to that team
      And the workflow reports a destination configuration error for that team