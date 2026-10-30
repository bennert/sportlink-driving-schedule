Feature: Exclude Costs And Technical Route Changes
  As a team contact
  I want cost and technical route differences excluded from change notifications
  So that I only receive explanations of relevant schedule changes

  Scenario Outline: Ignore a difference that does not change the practical schedule
    Given previous and current schedules differ only in "<field>"
      And all matches and schedule settings are otherwise identical
    When the schedule versions are compared
    Then there are no relevant change entries
      And no schedule-update email is requested

    Examples:
      | field                         |
      | travel cost per match         |
      | Dutch cost-per-kilometre line  |
      | English cost-per-kilometre line|
      | map URL                       |
      | legacy distance metric value  |
      | legacy duration metric value  |

  Scenario: Report a legacy match time adjustment without reporting costs
    Given both schedules lack source match identifiers
      And match "EHV HS1 - Team A" on "01-11-2026" is unique in both schedules
      And its collection time changes from "10:00" to "10:15"
      And its travel cost and kilometre rate also change
    When the schedule versions are compared
    Then exactly one match adjustment shows collection time "10:00" followed by "10:15"
      And no cost value or kilometre rate appears in the change entries
      And a schedule-update email is requested

  Scenario: Treat a different location name as a relevant change
    Given a reliably matched match changes location name from "Hall A" to "Hall B"
      And its map URL also changes
    When the schedule versions are compared
    Then the report contains exactly one location-name adjustment from "Hall A" to "Hall B"
      And the report contains no map-URL adjustment
