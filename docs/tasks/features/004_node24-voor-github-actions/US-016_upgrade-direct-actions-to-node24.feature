Feature: Upgrade Direct Actions To Node24
  As a schedule maintainer
  I want the direct workflow actions to declare Node.js 24
  So that the runner no longer needs to force those actions off their declared runtime

  Scenario Outline: Use a verified Node.js 24 reference for a direct action
    Given the driving-schedule workflow uses "<action>"
      And the selected replacement reference has been checked against its action metadata and release notes
    When the direct action references are migrated
    Then every direct use of "<action>" resolves to metadata declaring "node24"
      And the selected reference is a release tag or an immutable commit SHA
      And the selected reference and inspected metadata revision are recorded

    Examples:
      | action                   |
      | actions/checkout         |
      | actions/setup-python     |
      | actions/configure-pages  |
      | actions/deploy-pages     |
      | actions/upload-artifact  |

  Scenario: Preserve the ordinary artifact upload contract
    Given the workflow uploads schedules, change reports, cached place IDs, and PDFs
    When the upload-artifact steps are migrated
    Then the upload contract is exactly
      | name                       | paths                                         | retention days |
      | driving-schedules-md       | docs/*.md; docs/schedule_changes_*.json        | 30             |
      | google-maps-place-id-cache | docs/google_maps_place_ids.json               | 90             |
      | driving-schedules-pdf      | docs/*.pdf                                    | 90             |
      And the cache upload still requires successful schedule generation

  Scenario: Preserve workflow behavior without runtime override flags
    Given the existing workflow uses Python "3.11" on "ubuntu-latest"
      And its baseline includes the main push, manual dispatch, and Monday "0 6 * * 1" triggers
    When the direct action references are migrated
    Then the Python version, runner, triggers, existing permissions, step IDs, and output references are unchanged
      And no moving main, master, or HEAD action reference is introduced
      And "FORCE_JAVASCRIPT_ACTIONS_TO_NODE24" is not introduced
      And "ACTIONS_ALLOW_USE_UNSECURE_NODE_VERSION" is not introduced
      And email and Telegram conditions are unchanged
