# Feature Specification 001: Wekelijkse WhatsApp-wedstrijd-aankondiging

**Date:** 2026-10-28
**Status:** Draft
**Ideation:** [001: Wekelijkse aankondiging van de komende wedstrijd](../ideation/001_weekelijkse-wedstrijd-aankondiging.md)
**Stories:** US-001 through US-003
**Feature Files:**

- `docs/tasks/features/001_weekelijkse-wedstrijd-aankondiging/US-001_configure-whatsapp-ontvangers-per-team.feature`
- `docs/tasks/features/001_weekelijkse-wedstrijd-aankondiging/US-002_select-wedstrijden-voor-de-komende-zeven-dagen.feature`
- `docs/tasks/features/001_weekelijkse-wedstrijd-aankondiging/US-003_verstuur-de-wekelijkse-whatsapp-wedstrijd-aankondiging.feature`

## Context

De bestaande workflow maakt op maandag rijschema's vanuit de Sportlink-kalender en mailt PDF's alleen wanneer de schema-inhoud is gewijzigd. Teamcontacten willen daarnaast iedere week een WhatsApp-aankondiging van de wedstrijden in de komende zeven dagen, ook als het rijschema ongewijzigd is. De aankondiging bevat tegenstander, datum, aanvangstijd, locatie, verzameltijd, reistijd, afstand en reiskosten.

De bestaande Sportlink-verwerking en rijschema's leveren deze gegevens al. Er zijn nog geen WhatsApp-ontvangers of WhatsApp-verzendintegratie geconfigureerd. De gekozen oplossingsrichting is een provider zoals Twilio; de precieze provider/accountconfiguratie moet voor implementatie worden bevestigd.

## User Stories

### US-001 Configure WhatsApp Recipients Per Team

```text
AS A team coordinator
I WANT to configure opted-in WhatsApp recipients for each team
SO THAT weekly announcements reach the right team contacts
```

**Complexity:** S
**Feature File:** `docs/tasks/features/001_weekelijkse-wedstrijd-aankondiging/US-001_configure-whatsapp-ontvangers-per-team.feature`
**Acceptance Focus:**

- Each WhatsApp recipient is associated with exactly the intended team.
- Only valid, opted-in recipients are eligible to receive announcements.
- Missing or invalid recipient configuration is reported and does not send a message to an unintended number.
**Dependencies:** None.
**Notes:** Keep WhatsApp recipients separate from email addresses. Store phone numbers and provider credentials in protected configuration, not in source control. Use an internationally formatted phone number and record opt-in before enabling a recipient.

### US-002 Select Matches for the Coming Seven Days

```text
AS a team contact
I WANT the announcement to include matches in the next seven days
SO THAT I can plan match attendance and travel
```

**Complexity:** M
**Feature File:** `docs/tasks/features/001_weekelijkse-wedstrijd-aankondiging/US-002_select-wedstrijden-voor-de-komende-zeven-dagen.feature`
**Acceptance Focus:**

- Select matches starting at or after the workflow run time and before seven days after that time, using the Europe/Amsterdam timezone.
- Include opponent, date, start time, location, collection time, travel time, distance, and travel costs for each selected match.
- Produce no announcement when there are no matches in the window.
**Dependencies:** Existing Sportlink calendar retrieval and rijschema calculations.
**Notes:** The seven-day window is a rolling interval from the scheduled workflow run, not the remainder of the Monday-to-Sunday calendar week. Do not include driver names; no reliable driver assignment source exists today.

### US-003 Send the Weekly WhatsApp Match Announcement

```text
AS a team contact
I WANT to receive the weekly match announcement on WhatsApp
SO THAT I have the match and travel details without checking the PDF
```

**Complexity:** M
**Feature File:** `docs/tasks/features/001_weekelijkse-wedstrijd-aankondiging/US-003_verstuur-de-wekelijkse-whatsapp-wedstrijd-aankondiging.feature`
**Acceptance Focus:**

- Send the announcement on each scheduled Monday workflow run when matches and eligible recipients exist, even if the driving schedule has not changed.
- Send only to the configured opted-in recipients for that team.
- Report provider failures as failed workflow delivery; do not report a rejected message as successfully sent.
**Dependencies:** US-001, US-002; a provisioned WhatsApp provider account and sender; provider-approved message template if required.
**Notes:** The existing workflow runs at 06:00 UTC on Mondays. Confirm provider, sender registration, message-template requirements, recipient consent, and local delivery-time expectations before implementation. This story does not promise exactly-once delivery across workflow retries.

## Open Decisions

- Confirm whether Twilio is the provider or whether another WhatsApp provider will be used.
- Confirm the expected local delivery time; the existing 06:00 UTC schedule shifts in local time with daylight-saving changes.
- Confirm whether a WhatsApp message alone is sufficient or whether the existing PDF should also be attached or linked.
