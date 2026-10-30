Feature: Publish GitHub Pages Without Node20 Dependencies
  As a team contact
  I want the stable schedule links published without deprecated action dependencies
  So that the runtime migration does not interrupt access to current schedule PDFs

  Scenario: Remove indirect deprecated runtime dependencies from Pages upload
    Given the current Pages upload uses a composite action with a nested Node.js 20 action
    When the Pages artifact preparation and upload steps are migrated
    Then every reachable JavaScript action in those steps declares "node24"
      And all selected action references are verified release tags or reviewed immutable commit SHAs
      And no moving branch reference or runtime-forcing flag is used to meet the runtime requirement

  Scenario: Preserve the deployable Pages artifact format
    Given the generated site contains "index.html" and "teams/ehv-hs1/latest.pdf"
      And the packaging fixture also contains ".git", ".github", and ".env" files
    When the migrated Pages artifact is prepared and uploaded
    Then the artifact is named "github-pages" with retention of one day
      And it contains one "artifact.tar" with "index.html" and "teams/ehv-hs1/latest.pdf" at their site-relative paths
      And no additional nested archive is introduced
      And the archive contains no .git, .github, .env, symbolic-link, or hard-link entries
      And the archive contains no file from outside the generated site

  Scenario: Keep the stable schedule URL and deployment output working
    Given an approved test site has an existing stable team schedule link
      And an updated schedule PDF has been packaged by the migrated workflow
    When the controlled Pages deployment succeeds
    Then the existing stable link resolves to the updated PDF
      And the deployment step still exposes "page_url"
      And the environment URL still uses "steps.deployment.outputs.page_url"
      And the deployment uses the existing "github-pages" environment
