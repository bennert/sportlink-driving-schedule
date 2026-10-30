Feature: Compare Schedule Versions Per Team
  As a team contact
  I want to see which matches and schedule settings changed
  So that I can identify the practical differences without comparing entire documents

  Scenario Outline: Report old and new values for a reliably identified match or setting
    Given previous and current schedules for team "EHV HS1"
      And the same unique source identifier identifies the match in both versions
      And only the following value differs between the versions
        | field   | previous | current |
        | <field> | <old>    | <new>   |
    When the schedule versions are compared
    Then the report identifies team "EHV HS1"
      And exactly one change for "<field>" shows "<old>" followed by "<new>"
      And no added or removed match is reported

    Examples:
      | field            | old              | new              |
      | date             | 01-11-2026       | 08-11-2026       |
      | weekday          | Sunday           | Monday           |
      | description      | EHV HS1 - Team A | EHV HS1 - Team B |
      | collection time  | 10:00            | 10:15            |
      | start time       | 11:00            | 11:30            |
      | end time         | 13:00            | 13:30            |
      | location name    | Hall A           | Hall B           |
      | base location    | Eindhoven        | Veldhoven        |
      | warming-up time  | 00:45:00         | 01:00:00         |
      | document logo    | logos/old.png    | logos/new.png    |

  Scenario: Distinguish added and removed matches without claiming cancellation
    Given the previous schedule contains match "A" on "01-11-2026" and match "B" on "08-11-2026"
      And the current schedule contains unchanged match "A" and new match "C" on "15-11-2026"
    When the schedule versions are compared
    Then match "B" is reported as "Vervallen uit het schema" and "Removed from the schedule"
      And match "C" is reported as "Toegevoegd" and "Added"
      And match "A" has no change entry
      And the report does not describe match "B" as cancelled

  Scenario: Preserve ambiguous duplicate rows during legacy comparison
    Given neither schedule has source match identifiers
      And the previous schedule contains two matches with the same date and description at "11:00" and "15:00"
      And the current schedule contains two matches with that date and description at "11:30" and "15:30"
    When the schedule versions are compared
    Then the report contains exactly two removed matches and two added matches
      And no old-to-new time adjustment is claimed
      And neither duplicate match is discarded
