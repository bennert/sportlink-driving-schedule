Feature: Configure WhatsApp Recipients Per Team
  As a team coordinator
  I want to configure opted-in WhatsApp recipients for each team
  So that weekly announcements reach the right team contacts

  Scenario: Use configured recipients for their assigned team
    Given a team has valid WhatsApp recipients configured
      And each recipient has opted in to receive team announcements
    When the weekly announcement is prepared for that team
    Then only those recipients are eligible to receive that team's announcement
      And recipients configured for another team are excluded

  Scenario: Do not send to a team with invalid recipient configuration
    Given a team has a missing or invalid WhatsApp recipient number
    When the weekly announcement is prepared for that team
    Then no WhatsApp message is sent to that team
      And the workflow reports a recipient configuration error for that team