# sportlink-driving-schedule

Sportlink Driving Schedule

## Why this project?

As a team coordinator or volunteer at a sports club, you know the drill: every season, manually figuring out where away games are played, when to leave, and what the travel costs are. This manual work is time-consuming and error-prone.

**This project automates the entire process:**

- 📅 **Automatic synchronization** - Fetches match data directly from your Sportlink calendar
- 🗺️ **Smart route calculation** - Calculates distances and travel times to away games via Google Maps
- ⏰ **Departure times** - Determines when to gather based on warm-up time and travel duration  
- 💰 **Cost calculation** - Automatically calculates travel costs per kilometer
- 📧 **Automatic emails** - Sends weekly updated driving schedules as PDF to team members
- 🔄 **Always up-to-date** - Runs automatically every Monday via GitHub Actions

Save yourself (and your team) hours of work and prevent miscommunication about departure times and locations!

## Installation

### Fork this Repository

1. Click the "Fork" button at the top right of this repository
2. Clone your forked repository:

```bash
git clone https://github.com/YOUR_USERNAME/sportlink-driving-schedule.git
cd sportlink-driving-schedule
```

### Configure Environment Variables

This project requires the following environment variables:

#### Required Secrets

1. **MAPS_API_KEY**: Google Maps API key for calculating distances and travel times
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one
   - Enable the following APIs:
     - Distance Matrix API
     - Places API
   - Create credentials (API Key)
   - Copy the API key

2. **SPORTLINK_TOKEN_LIST**: Comma-separated list of team IDs with their Sportlink calendar tokens (sensitive)
   - Format: `TEAM_ID:token,TEAM_ID2:token2`
   - Example: `EHV DS1:abc123token,EHV DS2:def456token`
   - Each team can have its own Sportlink calendar token
   - Get your Sportlink calendar tokens from [Sportlink](https://www.sportlink.com/)

3. **SPORTLINK_TEAM_LIST**: Comma-separated list of team configurations
   - Format: `TEAM_ID:BASE_LOCATION:WARMUP_MINUTES:COST_PER_KM:TEAM_EMAIL`
   - Example: `EHV DS1:Strijp Rijstenweg 7:60:0.23:coach1@example.com,EHV DS2:Strijp Rijstenweg 7:45:0.23:coach2@example.com`
   - Each team can have its own email recipient for the driving schedule
   - Multiple email addresses per team can be separated by semicolons (e.g., `coach1@example.com;assistant@example.com`)

4. **EMAIL_USERNAME**: Gmail address for sending schedules (only needed for GitHub Actions)
   - Example: `your.email@gmail.com`

5. **EMAIL_PASSWORD**: Gmail app password for authentication (only needed for GitHub Actions)
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable 2-Step Verification if not already enabled
   - Go to App Passwords
   - Generate a new app password for "Mail"
   - Copy the generated 16-character password

6. **TELEGRAM_BOT_TOKEN**: Token for the Telegram bot that sends weekly match announcements
   - Create a bot with [BotFather](https://telegram.me/BotFather)
   - Store the token as a GitHub Actions secret; do not commit it to the repository

7. **TELEGRAM_CHAT_LIST**: Comma-separated team-to-chat mapping for Telegram announcements
   - Format: `TEAM_ID:CHAT_ID;CHAT_ID,TEAM_ID2:CHAT_ID2`
   - Example: `EHV DS1:-1001234567890;123456789,EHV HS1:-1009876543210`
   - A private recipient must start the bot first; add the bot to a group before using that group's chat ID

#### Setting up Secrets Locally

Create a `.env` file in the root directory:

```bash
MAPS_API_KEY=your_google_maps_api_key_here
SPORTLINK_TOKEN_LIST=TEAM_ID:team_sportlink_calendar_token
# Example with multiple teams:
# SPORTLINK_TOKEN_LIST=EHV DS1:abc123token,EHV DS2:def456token
SPORTLINK_TEAM_LIST=TEAM_ID:BASE_LOCATION:WARMUP_MINUTES:COST_PER_KM:TEAM_EMAIL
# Example with multiple teams and recipients:
# SPORTLINK_TEAM_LIST=EHV DS1:Strijp 7:60:0.23:coach1@example.com;assistant1@example.com,EHV DS2:Strijp 7:45:0.23:coach2@example.com
EMAIL_USERNAME=your.email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_SUBJECT=Driving Schedule of your club
EMAIL_FROM=Scheduler <your.email@gmail.com>
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_LIST=TEAM_ID:CHAT_ID;CHAT_ID,TEAM_ID2:CHAT_ID2
```

#### Setting up Secrets in GitHub

If you're using GitHub Actions or want to store secrets securely:

1. Go to your forked repository on GitHub
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets:
   - Name: `MAPS_API_KEY`, Value: your Google Maps API key
   - Name: `SPORTLINK_TOKEN_LIST`, Value: Your team Sportlink tokens (format: `TEAM_ID:token,TEAM_ID2:token2`)
   - Name: `EMAIL_USERNAME`, Value: your Gmail address
   - Name: `EMAIL_PASSWORD`, Value: your Gmail app password
   - Name: `TELEGRAM_BOT_TOKEN`, Value: your Telegram bot token
   - Name: `TELEGRAM_CHAT_LIST`, Value: your team-to-chat mappings

5. Click on **Variables** tab and add the following variables:
   - Name: `SPORTLINK_TEAM_LIST`, Value: your team configuration(s) including email per team
   - Name: `EMAIL_SUBJECT`, Value: your email subject (e.g., "Driving Schedule")
   - Name: `EMAIL_FROM`, Value: sender name and email (e.g., `Scheduler <your.email@gmail.com>`)

### Create Virtual Environment

1. Create a new virtual environment:

```bash
python -m venv .venv
```

1. Activate the virtual environment:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# Linux/Mac
source .venv/bin/activate
```

1. Install the dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Google Maps place ID cache

GitHub Actions persists a cache mapping normalized Sportlink locations to Google Maps `place_id` values. It does not store Distance Matrix distances or durations. Those route values are requested again during each schedule run. The cache is stored as the `google-maps-place-id-cache` workflow artifact.

### Generate driving schedule

```bash
python create_driving_schedule.py
```

### Understand schedule changes

Schedule update emails include the complete change report in Dutch and English. Each PDF includes the report in its own language, on new pages after the schedule table. GitHub Actions also shows the current run's changes per team in its run summary, before email delivery.

Reports show added and removed matches, old and new match details, and changed schedule settings. A removed match is not automatically a cancelled match. Comparisons use the previous available schedule, not a confirmed last-delivered email. Missing or unreadable previous versions are explicitly identified.

Travel costs, kilometre rates, route metric values, and map URL changes do not trigger update emails or appear in change entries. Costs remain visible in the full schedule. Without relevant changes, no update email is sent and the PDF keeps the report belonging to its current version.

The latest report and source match identifiers are stored in per-team JSON files alongside the Markdown schedules and retained in the `driving-schedules-md` artifact. Restore those files together. Invalid reports or reports for another schedule version block update delivery rather than silently dropping the explanation. Legacy schedules without reports show an explicit unavailable-report notice.

### Convert driving schedule to PDF

```bash
python convert_driving_schedule_to_pdf.py
```

### Run the tests

Install the test dependencies in the activated virtual environment, then run:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -v
```

Tests use local fixtures and mocked external services. PDF tests generate both languages, extract text, render report pages, and check pagination and text bounds.

### GitHub Actions Node.js 24 migration

The schedule workflow pins reviewed action commits. The release versions, exact revisions, runtime declarations, used inputs, nested dependencies, and compatibility notes are recorded in [.github/action-runtime-audit.json](.github/action-runtime-audit.json). This includes both ordinary artifact uploads and the separate uploader inside the Pages composite.

After installing the test dependencies, run the local checks from the repository root:

```bash
python -m unittest discover -v
actionlint -shellcheck= -pyflakes= .github/workflows/driving_schedule.yml
python audit_action_runtimes.py
```

The unit tests stay offline and require GNU tar for the Pages archive fixture. On Windows they use Git for Windows' bundled tar when available. The final command is an explicit, read-only network audit: it downloads action metadata at the pinned commits and checks runtimes, inputs, defaults, nested references, and the Linux Pages tar command. It does not execute downloaded actions, dispatch workflows, deploy Pages, or send messages. The actionlint invocation checks workflow syntax and inputs; optional ShellCheck and Pyflakes integrations are disabled in this environment.

Local verification on 2026-10-30:

- **Passed:** 68 unit tests, including workflow settings, artifact names/paths/retention, dependency-audit failures, and the Pages tar fixture. The fixture retains site-relative HTML/PDF paths, excludes hidden files, and converts hardlinks to ordinary archive entries.
- **Passed:** actionlint 1.7.12, installed from its official release after verifying the published SHA-256 checksum.
- **Passed:** read-only upstream metadata audit of eight pinned references: seven JavaScript actions declare Node.js 24 and one Pages composite depends only on the reviewed Node.js 24 uploader.
- **Pending:** an approved test environment, controlled workflow run URL, cross-run restoration of Markdown/JSON/cache artifacts, empty-history behavior on GitHub, token permission verification, Pages deployment, stable PDF URL, and absence of the Node.js 20 warning in an actual run.

The migration is locally implemented but is **not fully accepted** until the pending checks pass. No production workflow was dispatched for validation. A push to `main` or a manual dispatch can publish schedules and send team email; do not use that as an uncontrolled migration test.

Before a live validation, explicitly approve a test repository or controlled environment with test notification destinations and a test Pages site. Run once without previous artifacts and again with previous artifacts, verify the restored JSON report matches its schedule version, verify the published team PDF and deployment URL, and record the run URLs and warning check here or in the migration PR. Keep production triggers and destinations unchanged. For private repositories the download action documents `actions: read` as necessary; existing permissions remain unchanged until documentation and a controlled restore test justify that minimal addition. Do not replace it with a personal access token or write permission.

### Adding Team Logos

You can add team and/or club logos to each driving schedule:

1. **Create a logos folder** in the project root:

   ```bash
   mkdir logos
   ```

2. **Add logo files** with the following naming convention:
   - Convert the team ID to lowercase
   - Replace spaces with underscores
   - Add `.team.png` or `.club.png` suffix

   **Examples:**
   - Team "EHV DS1" team logo → `logos/ehv_ds1.team.png`
   - Team "EHV DS1" club logo → `logos/ehv_ds1.club.png`
   - Team "EHV HS1" club logo → `logos/ehv_hs1.club.png`
   - Team "My Team U15" team logo → `logos/my_team_u15.team.png`

3. **Logo placement:**
   - **Club logo**: Displayed on the left side next to the team information
   - **Team logo**: Displayed on the right side next to the team information
   - Both logos are shown horizontally aligned on the right side of the page
   - You can use one or both logos per team

4. **Logo requirements:**
   - Format: PNG (recommended for transparency)
   - Logos will be displayed at 2cm height with preserved aspect ratio
   - Logos are automatically detected and added if the file exists
   - If no logo exists for a team, the schedule is generated without it

5. **Run the scripts** as normal - logos will be automatically included in both markdown and PDF outputs
