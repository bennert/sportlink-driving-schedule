"""
Script to send driving schedule PDFs per team via email
"""
import os
import sys
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def send_email(
    email_to,
    email_subject,
    email_body,
    email_pdf_files,
    email_from,
    scheduler_id,
    smtp_username,
    smtp_password):
    """Send email with PDF attachments

    Args:
        email_to: Email address(es). Multiple addresses can be separated by semicolons (;)
    """
    if not email_to or email_to.strip() == '':
        print("  Skipping email - no recipient configured")
        return False

    if not email_body or email_body.strip() == '':
        print("  Skipping email - no message body")
        return False

    if not email_pdf_files or len(email_pdf_files) == 0:
        print("  Skipping email - no PDF files to attach")
        return False

    # Split multiple email addresses by semicolon
    to_emails = [email.strip() for email in email_to.split(';') if email.strip()]

    msg = MIMEMultipart()
    msg['From'] = f"Scheduler {scheduler_id}<{email_from}>"
    msg['To'] = ', '.join(to_emails)  # Join with comma for email header
    msg['Subject'] = email_subject

    msg.attach(MIMEText(email_body, 'plain'))

    # Attach PDF files
    for pdf_file in pdf_files:
        if os.path.exists(pdf_file):
            with open(pdf_file, 'rb') as file_email:
                pdf_attachment = MIMEApplication(file_email.read(), _subtype='pdf')
                pdf_attachment.add_header('Content-Disposition', 'attachment',
                                         filename=os.path.basename(pdf_file))
                msg.attach(pdf_attachment)

    try:
        # Connect to Gmail SMTP server
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(smtp_username, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"  Email sent successfully to {email_to}")
        return True
    except (smtplib.SMTPAuthenticationError, smtplib.SMTPException, OSError) as e:
        print(f"  Failed to send email to {email_to}: {e}")
        return False

# Get email credentials from environment
username = os.getenv('EMAIL_USERNAME')
password = os.getenv('EMAIL_PASSWORD')
mail_from = os.getenv('EMAIL_FROM', username)
email_subject_prefix = os.getenv('EMAIL_SUBJECT', 'Driving Schedule')

if not username or not password:
    print("ERROR: EMAIL_USERNAME and EMAIL_PASSWORD must be set")
    sys.exit(1)

# Input paths
script_dir = os.path.dirname(os.path.abspath(__file__))
handbal_folder = os.path.join(script_dir, "docs")

# Check for flag files that indicate which teams have changes
flag_files = [file for file in os.listdir(handbal_folder) if file.endswith(".flag")]

if not flag_files:
    print("No flag files found - no emails to send")
    sys.exit(0)

print(f"\nFound {len(flag_files)} team(s) with changes")

# Process each team
EMAILS_SENT = 0
for flag_file in flag_files:
    flag_path = os.path.join(handbal_folder, flag_file)
    team_id = flag_file.replace('.convert_to_pdf_', '').replace('.flag', '')

    print(f"\nProcessing team: {team_id}")

    with open(flag_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    # Remove the flag file after reading
    os.remove(flag_path)
    print(f"  Flag file removed: {flag_file}")

    if len(lines) < 3:
        print(f"  WARNING: Flag file incomplete for {team_id}")
        continue

    nl_file = lines[0]
    en_file = lines[1]
    team_email = lines[2] if len(lines) > 2 else ''

    # Get corresponding PDF files
    pdf_nl = nl_file.replace('.md', '.pdf')
    pdf_en = en_file.replace('.md', '.pdf')

    pdf_files = []
    if os.path.exists(pdf_nl):
        pdf_files.append(pdf_nl)
    if os.path.exists(pdf_en):
        pdf_files.append(pdf_en)

    if not pdf_files:
        print(f"  WARNING: No PDF files found for {team_id}")
        continue

    # Prepare email
    SUBJECT = f"{email_subject_prefix} - {team_id} - {datetime.now().strftime('%Y-%m-%d')}"
    BODY = f"""New driving schedule generated for {team_id}!

See the attached PDF file(s).

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""

    # Send email
    if send_email(team_email,
                  SUBJECT,
                  BODY,
                  pdf_files,
                  email_from=mail_from,
                  scheduler_id=team_id,
                  smtp_username=username,
                  smtp_password=password):
        EMAILS_SENT += 1

print(f"\n{'='*50}")
print(f"Email summary: {EMAILS_SENT} email(s) sent successfully")
print(f"{'='*50}")

if EMAILS_SENT == 0:
    sys.exit(1)
