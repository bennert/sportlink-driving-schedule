# sportlink-driving-schedule
Sportlink Driving Schedule

## Installation

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
