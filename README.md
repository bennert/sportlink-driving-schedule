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

5. Click on **Variables** tab and add the following variables:
   - Name: `SPORTLINK_TEAM_LIST`, Value: your team configuration(s) including email per team
   - Name: `EMAIL_SUBJECT`, Value: your email subject (e.g., "Driving Schedule")
   - Name: `EMAIL_FROM`, Value: sender name and email (e.g., "Scheduler \<your.email@gmail.com\>")

### Create Virtual Environment

1. Create a new virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

# Windows (Command Prompt)
.venv\Scripts\activate.bat

# Linux/Mac
source .venv/bin/activate
```

3. Install the dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Generate driving schedule
```bash
python create_driving_schedule.py
```

### Convert driving schedule to PDF
```bash
python convert_driving_schedule_to_pdf.py
```
