
import imaplib
import email
import json
import smtplib
from email.message import EmailMessage
import pandas as pd
from datetime import datetime
import time
from bs4 import BeautifulSoup

EMAIL_ADDRESS = 'usmanrashidkhan321@gmail.com'
EMAIL_PASSWORD = 'fmzyvwnsorlgexva'

def get_valid_clients():
    valid_clients = []
    today = datetime.now().date()
    try:
        df = pd.read_excel('clients.csv.xlsx')
        for _, row in df.iterrows():
            expiry_date = pd.to_datetime(row['expiry']).date()
            if expiry_date >= today:
                valid_clients.append(row['email'])
    except Exception as e:
        print(f"Error reading client list: {e}")
    return valid_clients

def send_email_to_clients(subject, message_body):
    clients = get_valid_clients()
    for email_to in clients:
        try:
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = email_to
            msg.set_content(message_body)

            with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
                smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
                smtp.send_message(msg)
                print(f"✅ Email sent to {email_to}")
        except Exception as e:
            print(f"❌ Failed to send to {email_to}: {e}")

def format_alert_message(alert_data):
    return f"""
TradingView Signal Alert

Pair: {alert_data.get('pair', 'Unknown')}
Price: {alert_data.get('price', 'N/A')}
Signal: {alert_data.get('signal', '').upper()}

Please check your chart and take action accordingly.
Alert Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Regards,
AlphaFX Signals
AlphaFX Team
Contact Admin if you need access renewal
"""

def check_latest_email():
    try:
        mail = imaplib.IMAP4_SSL('imap.gmail.com')
        mail.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        mail.select('inbox')

        status, messages = mail.search(None, 'ALL')
        email_ids = messages[0].split()

        if not email_ids:
            print("No emails found.")
            return

        latest_email_id = email_ids[-1]
        status, msg_data = mail.fetch(latest_email_id, '(RFC822)')

        for response_part in msg_data:
            if isinstance(response_part, tuple):
                msg = email.message_from_bytes(response_part[1])
                print("📧 Subject Found:", msg["Subject"])

                if msg.is_multipart():
                    for part in msg.walk():
                        if part.get_content_type() in ['text/plain', 'text/html']:
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = msg.get_payload(decode=True).decode()

                print("📩 EMAIL BODY RECEIVED:")
                print(body)

                soup = BeautifulSoup(body, "html.parser")
                text = soup.get_text(separator="\n").strip()

                print("📄 Plain Text Extracted:")
                print(text)

                json_body = None
                for line in text.splitlines():
                    if line.strip().startswith("{") and '"signal"' in line:
                        json_body = line.strip()
                        break

                if not json_body:
                    print("⚠️ No valid JSON found after stripping HTML")
                    return

                try:
                    alert_data = json.loads(json_body)
                    subject = f"{alert_data.get('signal', '').upper()} Signal Alert - {alert_data.get('pair', 'XAUUSD')}"
                    message_body = format_alert_message(alert_data)
                    send_email_to_clients(subject, message_body)
                except Exception as e:
                    print(f"❌ Failed to parse/send email: {e}")
        mail.logout()

    except Exception as e:
        print(f"⚠️ Gmail check failed: {e}")

if __name__ == "__main__":
    print("📬 AlphaFX Gmail Alert Reader Running (with BeautifulSoup)...")
    while True:
        check_latest_email()
        time.sleep(60)
