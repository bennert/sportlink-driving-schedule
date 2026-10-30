Feature: Verify The Node24 Migration Without Production Notifications
  As a schedule maintainer
  I want recorded static checks and a controlled workflow run for the migration
  So that I can confirm warning removal without sending unintended team updates

  Scenario: Record passing local migration checks without contacting production services
    Given all migrated action references and resolved dependency metadata are available for inspection
      And workflow fixtures cover artifact paths and the Pages archive
    When the workflow lint, dependency audit, fixture checks, and Python regression suite run
    Then workflow syntax and used action inputs pass validation
      And the dependency audit finds no JavaScript action declaring Node.js 20
      And the artifact and Pages archive contract checks pass
      And the existing Python regression suite passes
      And selected references, resolved revisions, and command results are recorded
      And no production workflow, deployment, email, or Telegram delivery is triggered by the local checks

  Scenario: Confirm warning removal in an approved test environment
    Given the maintainer has explicitly approved a test repository or controlled test environment
      And only test notification destinations and a test Pages site are configured
      And local migration checks have passed
      And previous test artifacts are available
    When the migrated workflow is executed in that environment
    Then the workflow completes successfully
      And the run contains no "Node.js 20 is deprecated" warning
      And previous schedule files, JSON reports, and cached place IDs are restored successfully
      And the test Pages deployment publishes the current PDF at its stable link
      And no production notification destination receives a message
      And the run URL, artifact results, Pages result, and warning check are recorded

  Scenario: Keep remote verification pending without an approved test environment
    Given local migration checks have passed
      And no approved environment is available for a live workflow run
    When the migration verification results are reported
    Then local checks are reported as passed
      And remote warning-removal and deployment verification are reported as pending
      And the migration is not reported as fully accepted
      And no production workflow is dispatched to obtain missing evidence
