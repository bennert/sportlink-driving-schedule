Feature: Select Matches for the Coming Seven Days
  As a team contact
  I want the announcement to include matches in the next seven days
  So that I can plan match attendance and travel

  Scenario: Include all matches inside the seven-day window
    Given the Sportlink calendar contains matches inside and outside the next seven days
    When the weekly announcement is prepared at the scheduled workflow run time
    Then every match starting at or after the run time and before seven days later is included
      And matches outside that interval are excluded

  Scenario: Include the required match and travel details
    Given a match inside the seven-day window has a calculated driving schedule
    When its announcement details are prepared
    Then the details include opponent, date, start time, and location
      And the details include collection time, travel time, distance, and travel costs

  Scenario: No matches fall inside the seven-day window
    Given the Sportlink calendar has no match inside the next seven days
    When the weekly announcement is prepared
    Then no announcement is produced for that team
      And the workflow reports that there are no matches in the announcement window