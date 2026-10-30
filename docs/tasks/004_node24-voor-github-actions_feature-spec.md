# Feature Specification 004: Node.js 24 voor GitHub Actions

**Date:** 2026-10-30
**Status:** Draft
**Ideation:** [004: Node.js 24 voor GitHub Actions](../ideation/004_node24-voor-github-actions.md)
**Stories:** US-016 through US-019
**Feature Files:**

- [US-016_upgrade-direct-actions-to-node24.feature](features/004_node24-voor-github-actions/US-016_upgrade-direct-actions-to-node24.feature)
- [US-017_restore-previous-artifacts-with-node24.feature](features/004_node24-voor-github-actions/US-017_restore-previous-artifacts-with-node24.feature)
- [US-018_publish-github-pages-without-node20-dependencies.feature](features/004_node24-voor-github-actions/US-018_publish-github-pages-without-node20-dependencies.feature)
- [US-019_verify-the-node24-migration-without-production-notifications.feature](features/004_node24-voor-github-actions/US-019_verify-the-node24-migration-without-production-notifications.feature)

## Context

The driving-schedule workflow reports deprecated Node.js 20 actions being forced to run on Node.js 24. Upgrading the Python interpreter or installing Node.js in a workflow step does not change the JavaScript runtime declared by those actions. The migration must update the action dependencies themselves, including dependencies inside composite actions.

Ideation 004 identifies five verified direct upgrade candidates and two unresolved dependency choices: restoring artifacts from earlier runs and preparing the Pages artifact. This specification turns those findings into bounded implementation stories. No workflow changes or remote runs are performed by creating this specification.

## Scope And Rules

- Change action dependencies and only the compatibility adjustments necessary to preserve the existing workflow. Retain the Python version `3.11`, `ubuntu-latest`, application behavior, update-email conditions, weekly Telegram conditions, deployment step ID, and schedule-generation step outputs.
- Preserve the `main` push trigger, manual dispatch, and Monday `0 6 * * 1` schedule. Preserve the `github-pages` environment and `steps.deployment.outputs.page_url` reference.
- Keep existing permissions. Add `actions: read` only when upstream documentation and a controlled restore test demonstrate that it is required. Do not grant `actions: write` or introduce a personal access token for restoring artifacts. Do not expand repository or deployment permissions as a blanket migration workaround.
- Every selected JavaScript action, including actions reached through composite dependencies, must declare `runs.using: node24` in the exact referenced metadata. Shell-only composite steps are permitted. Merely forcing a Node.js 20 action onto Node.js 24 does not satisfy this requirement.
- Use a verified release tag or a reviewed immutable commit SHA. Do not use moving `main`, `master`, or `HEAD` references. Record the chosen reference, inspected metadata revision, declared runtime, required inputs, and relevant release-note compatibility findings. Major tags must be resolved again during implementation; findings from the ideation are not a permanent guarantee.
- Prefer a published Node.js 24 release of the existing artifact-download and Pages-upload actions. When a suitable release is absent, use a reviewed immutable Node.js 24 commit of the same upstream action or the bounded fallback described in the owning story. Do not add a new third-party action provider to solve this migration without separate approval.
- Do not add runtime-force or insecure-runtime environment flags to suppress warnings. A successful Python test run alone does not establish a successful runner migration.
- Keep three ordinary artifact uploads: `driving-schedules-md` for `docs/*.md` and `docs/schedule_changes_*.json` with 30-day retention; `google-maps-place-id-cache` for `docs/google_maps_place_ids.json` with 90-day retention; and `driving-schedules-pdf` for `docs/*.pdf` with 90-day retention. Preserve the cache-upload success condition.
- Restore both previous artifact types into `docs/` using the existing workflow selector `driving_schedule.yml` and existing successful-run selection behavior. Preserve the no-artifact-found tolerance and existing `continue-on-error` behavior. Do not silently restore only the current run or replace historical JSON reports with empty state.
- Validate remote behavior only in a test repository or an explicitly approved controlled environment. Do not dispatch the existing production workflow merely to test these stories: it can publish Pages and send email. No live run is authorized by this specification alone.
- Final acceptance requires both local checks and a recorded controlled GitHub Actions run. Record incomplete remote verification as pending, not passed. A live test that is blocked by access or credentials does not permit lowering the acceptance criteria.

## User Stories

### US-016 Upgrade Direct Actions To Node24

```text
AS A schedule maintainer
I WANT the direct workflow actions to declare Node.js 24
SO THAT the runner no longer needs to force those actions off their declared runtime
```

**Complexity:** M
**Feature File:** [US-016_upgrade-direct-actions-to-node24.feature](features/004_node24-voor-github-actions/US-016_upgrade-direct-actions-to-node24.feature)
**Acceptance Focus:**

- Upgrade checkout, setup-python, configure-pages, deploy-pages, and every ordinary upload-artifact step to verified Node.js 24 references.
- Preserve used inputs, outputs, artifact paths, retention periods, triggers, and application-runtime settings.
- Reject moving branch references and warning-suppression flags as migration substitutes.

**Dependencies:** Existing workflow; independently implementable before the two transitive dependency stories.
**Notes:** Initial candidates verified in Ideation 004 are checkout v5, setup-python v6, configure-pages v6, deploy-pages v5, and upload-artifact v6. Recheck each referenced action.yml and release notes. Upload-artifact v5 was inspected and still declared Node.js 20; do not assume one major increment is sufficient. Until US-017 and US-018 are complete, this story alone does not remove all deprecation warnings. Reuse an existing workflow test location where practical; otherwise one focused workflow test module is sufficient for the static contracts across these stories.

### US-017 Restore Previous Artifacts With Node24

```text
AS A schedule maintainer
I WANT previous schedules and the place-ID cache restored by Node.js 24-compatible actions
SO THAT runtime upgrades do not lose the comparison baseline or cached locations
```

**Complexity:** M
**Feature File:** [US-017_restore-previous-artifacts-with-node24.feature](features/004_node24-voor-github-actions/US-017_restore-previous-artifacts-with-node24.feature)
**Acceptance Focus:**

- Both download steps use verified Node.js 24 dependencies and still find the previous successful workflow's artifacts.
- Restore Markdown, JSON change reports, and cache contents with their existing names and `docs/` layout.
- Missing artifacts remain tolerated without manufacturing a comparison history or populated cache.

**Dependencies:** Existing artifact-download steps; the runtime inventory from US-016 can be reused but the story can be implemented independently.
**Notes:** The preferred path is a suitable release or reviewed immutable commit of dawidd6/action-download-artifact. The inspected v11 still declares Node.js 20; master declaring Node.js 24 is not a suitable moving reference. The alternative official download action requires an explicit previous-run lookup and a verified Node.js 24 dependency chain. That lookup must preserve the existing successful-run selection and not substitute the current run. If that alternative exceeds a single M pass, choose the reviewed upstream commit path or split the alternative before implementation. Metadata checks are local; cross-run download acceptance belongs to the controlled run in US-019.

### US-018 Publish GitHub Pages Without Node20 Dependencies

```text
AS A team contact
I WANT the stable schedule links published without deprecated action dependencies
SO THAT the runtime migration does not interrupt access to current schedule PDFs
```

**Complexity:** M
**Feature File:** [US-018_publish-github-pages-without-node20-dependencies.feature](features/004_node24-voor-github-actions/US-018_publish-github-pages-without-node20-dependencies.feature)
**Acceptance Focus:**

- Eliminate indirect Node.js 20 dependencies from Pages artifact preparation and upload.
- Preserve the `github-pages` deployment artifact, archive format, generated site files, and exclusions for repository metadata and secrets.
- Preserve working stable schedule links and the deployment URL output.

**Dependencies:** US-016 for the compatible upload-artifact and deploy-pages actions; existing site generation from US-007.
**Notes:** Inspect all nested action references: the inspected upload-pages-artifact v4 still references upload-artifact v4.6.2. Prefer a verified compatible release or reviewed immutable commit of the existing Pages-upload action. The bounded fallback is a shell packaging step on Ubuntu followed by the verified upload-artifact reference. Match the existing Pages artifact contract: upload a single `artifact.tar` containing site files at its root, without symbolic-link or hard-link entries, using the compatible upload action's artifact transport. Do not introduce an additional nested archive. Preserve the `github-pages` artifact name, one-day Pages-artifact retention, and existing paths such as `index.html` and `teams/<team-slug>/latest.pdf`. Exclude `.git`, `.github`, `.env`, and files outside the generated site. Do not upload the site directory directly as a presumed equivalent. Verify the archive locally before a controlled deployment.

### US-019 Verify The Node24 Migration Without Production Notifications

```text
AS A schedule maintainer
I WANT recorded static checks and a controlled workflow run for the migration
SO THAT I can confirm warning removal without sending unintended team updates
```

**Complexity:** M
**Feature File:** [US-019_verify-the-node24-migration-without-production-notifications.feature](features/004_node24-voor-github-actions/US-019_verify-the-node24-migration-without-production-notifications.feature)
**Acceptance Focus:**

- Validate workflow syntax, action inputs, the complete action runtime inventory, artifact contracts, and the existing Python regression suite.
- Record a successful controlled run showing cross-run restoration, Pages publication, and absence of the Node.js 20 runtime warning.
- Keep remote validation explicitly pending when no approved test environment is available.

**Dependencies:** US-016, US-017, US-018; separately approved test repository or controlled environment for live checks.
**Notes:** Use actionlint for workflow validation and the repository's existing `python -m unittest discover -v` gate after installing test requirements. Validate exact resolved metadata for remote actions in a separate, explicit dependency audit; normal unit tests must not require network access. Local fixture checks cannot prove a particular remote action's runtime. Document selected references, command results, controlled run URL, artifact results, Pages result, and warning check in the migration PR or a concise existing documentation section. Use only test destinations and test-site publication; do not change production notification triggers to make testing easier. No new deployment platform or general-purpose action updater is in scope.

## Implementation And Verification Order

1. Implement US-016, then US-017 and US-018. Each story can run local fixture checks before remote access is available.
2. Implement the local validation and evidence checklist in US-019. Execute the live portion only after the environment is explicitly approved.
3. Keep the migration unaccepted until all four stories' local checks pass and the controlled-run evidence is recorded. Do not claim the warning has disappeared on the strength of action references alone.

The feature files specify acceptance behavior. They do not include step implementations, and creating them does not execute BDD tests or authorize a production workflow run. Start implementation with `/coder` after reviewing this draft.
