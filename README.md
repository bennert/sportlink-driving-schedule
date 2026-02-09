# sportlink-driving-schedule
Sportlink Driving Schedule

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

2. **SPORTLINK_TOKEN_LIST**: Comma-separated list of team configurations
   - Format: `TEAM_ID:BASE_LOCATION:SPORTLINK_TOKEN:WARMUP_MINUTES:COST_PER_KM`
   - Example: `DHC1:Eindhoven:abc123token:30:0.23,DHC2:Eindhoven:def456token:45:0.23`
   - Get your Sportlink calendar token from [Sportlink](https://www.sportlink.com/)

3. **EMAIL_USERNAME**: Gmail address for sending schedules (only needed for GitHub Actions)
   - Example: `your.email@gmail.com`

4. **EMAIL_PASSWORD**: Gmail app password for authentication (only needed for GitHub Actions)
   - Go to [Google Account Security](https://myaccount.google.com/security)
   - Enable 2-Step Verification if not already enabled
   - Go to App Passwords
   - Generate a new app password for "Mail"
   - Copy the generated 16-character password

#### Setting up Secrets Locally

Create a `.env` file in the root directory:
```bash
MAPS_API_KEY=your_google_maps_api_key_here
SPORTLINK_TOKEN_LIST=TEAM_ID:BASE_LOCATION:SPORTLINK_TOKEN:WARMUP_MINUTES:COST_PER_KM
EMAIL_USERNAME=your.email@gmail.com
EMAIL_PASSWORD=your_app_password_here
```

#### Setting up Secrets in GitHub

If you're using GitHub Actions or want to store secrets securely:

1. Go to your forked repository on GitHub
2. Click on **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add the following secrets:
   - Name: `MAPS_API_KEY`, Value: your Google Maps API key
   - Name: `SPORTLINK_TOKEN_LIST`, Value: your team configuration string
   - Name: `EMAIL_USERNAME`, Value: your Gmail address
   - Name: `EMAIL_PASSWORD`, Value: your Gmail app password

5. Click on **Variables** tab and add the following variables:
   - Name: `EMAIL_SUBJECT`, Value: your email subject (e.g., "Driving Schedule")
   - Name: `EMAIL_TO`, Value: recipient email addresses (comma-separated)
   - Name: `EMAIL_FROM`, Value: sender name and email (e.g., "Scheduler <your.email@gmail.com>")

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
