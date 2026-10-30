Feature: Restore Previous Artifacts With Node24
  As a schedule maintainer
  I want previous schedules and the place-ID cache restored by Node.js 24-compatible actions
  So that runtime upgrades do not lose the comparison baseline or cached locations

  Scenario: Restore previous schedule files and their change report together
    Given a previous successful "driving_schedule.yml" run contains artifact "driving-schedules-md"
      And that artifact contains a Dutch schedule, an English schedule, and their team JSON change report
      And the current run has no schedule artifact of its own
    When the migrated schedule restore step runs
    Then the previous artifact files are restored under "docs/" with unchanged contents
      And the JSON report remains associated with the restored schedule version
      And the restore action dependency chain declares Node.js 24 for every JavaScript action
      And the selected download reference is recorded as a verified release tag or reviewed immutable commit SHA

  Scenario: Restore cached locations from the previous successful run
    Given a previous successful "driving_schedule.yml" run contains artifact "google-maps-place-id-cache"
      And the artifact contains "google_maps_place_ids.json" with existing location mappings
    When the migrated cache restore step runs
    Then the file is restored as "docs/google_maps_place_ids.json"
      And its stored location mappings are unchanged
      And the restore step retains the existing successful-workflow selection behavior
      And no personal access token or actions-write permission is introduced

  Scenario Outline: Continue without inventing state when an artifact is absent
    Given no previous matching artifact named "<artifact>" exists
    When its migrated restore step runs
    Then the workflow continues under the existing missing-artifact policy
      And the step retains its continue-on-error setting
      And no populated historical file is fabricated

    Examples:
      | artifact                   |
      | driving-schedules-md       |
      | google-maps-place-id-cache |
