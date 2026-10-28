# Feature Specification 001: Wekelijkse Telegram-wedstrijd-aankondiging

**Date:** 2026-10-28
**Status:** Draft
**Ideation:** [001: Wekelijkse aankondiging van de komende wedstrijd](../ideation/001_weekelijkse-wedstrijd-aankondiging.md)
**Stories:** US-001 through US-003
**Feature Files:**

- `docs/tasks/features/001_weekelijkse-wedstrijd-aankondiging/US-001_configure-telegram-bestemmingen-per-team.feature`
- `docs/tasks/features/001_weekelijkse-wedstrijd-aankondiging/US-002_select-wedstrijden-voor-de-komende-zeven-dagen.feature`
- `docs/tasks/features/001_weekelijkse-wedstrijd-aankondiging/US-003_verstuur-de-wekelijkse-telegram-wedstrijd-aankondiging.feature`

## Context

De bestaande workflow maakt op maandag rijschema's vanuit de Sportlink-kalender en mailt PDF's alleen wanneer de schema-inhoud is gewijzigd. Teamcontacten willen daarnaast iedere week een Telegram-aankondiging van de wedstrijden in de komende zeven dagen, ook als het rijschema ongewijzigd is. De aankondiging bevat tegenstander, datum, aanvangstijd, locatie, verzameltijd, reistijd, afstand en reiskosten.

De bestaande Sportlink-verwerking en rijschema's leveren deze gegevens al. Er zijn nog geen Telegram-chatbestemmingen of botintegratie geconfigureerd. De gekozen verzendroute is de Telegram Bot API. Privéontvangers moeten de bot eerst starten; voor een groepsbestemming moet de bot aan de groep zijn toegevoegd.

## User Stories

### US-001 Configure Telegram Destinations Per Team

```text
AS A team coordinator
I WANT to configure Telegram chat destinations for each team
SO THAT weekly announcements reach the right team contacts
```

**Complexity:** S
**Feature File:** `docs/tasks/features/001_weekelijkse-wedstrijd-aankondiging/US-001_configure-telegram-bestemmingen-per-team.feature`
**Acceptance Focus:**

- Each configured Telegram chat destination is associated with exactly the intended team.
- Private recipients have started the bot, or the bot has been added to the configured group.
- Missing or invalid chat configuration is reported and does not send a message to an unintended chat.
**Dependencies:** A Telegram bot has been created.
**Notes:** Keep Telegram chat IDs separate from email addresses. Store the bot token as a protected secret, not in source control. Do not include sensitive personal information in bot messages.

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

### US-003 Send the Weekly Telegram Match Announcement

```text
AS a team contact
I WANT to receive the weekly match announcement on Telegram
SO THAT I have the match and travel details without checking the PDF
```

**Complexity:** M
**Feature File:** `docs/tasks/features/001_weekelijkse-wedstrijd-aankondiging/US-003_verstuur-de-wekelijkse-telegram-wedstrijd-aankondiging.feature`
**Acceptance Focus:**

- Send the announcement on each scheduled Monday workflow run when matches and eligible recipients exist, even if the driving schedule has not changed.
- Send only to the configured Telegram chat destinations for that team.
- Report Bot API failures as failed workflow delivery; do not report a rejected request as successfully sent.
**Dependencies:** US-001, US-002; Telegram bot token and configured chat destinations.
**Notes:** The existing workflow runs at 06:00 UTC on Mondays. Confirm the local delivery-time expectation and check Telegram Bot API rate limits before implementation. This story does not promise exactly-once delivery across workflow retries.

## Open Decisions

- Confirm whether each team will receive messages in a group chat, private chats, or both.
- Confirm who will create and manage the Telegram bot and its protected token.
- Confirm the expected local delivery time; the existing 06:00 UTC schedule shifts in local time with daylight-saving changes.
- Confirm whether a Telegram message alone is sufficient or whether the existing PDF should also be attached or linked.
