import requests
import datetime
import smtplib
from email.message import EmailMessage
from pathlib import Path

# ===== CONFIGURATION =====
LAT = 45.46
LON = 4.77
THRESHOLD = 1.0

EMAIL_TO = "spartan117vemasa@gmail.com"
EMAIL_FROM = "spartan117vemasa@gmail.com"

SMTP_SERVER = "SMTP_SERVEUR"
SMTP_PORT = 587
SMTP_USER = "SMTP_USER"
SMTP_PASS = "SMTP_PASSWORD"

STATE_FILE = Path("last_email_sent.txt")
TODAY = datetime.date.today().isoformat()

# ===== LIMITE 1 MAIL / JOUR =====
if STATE_FILE.exists() and STATE_FILE.read_text() == TODAY:
    exit()

# ===== METEO =====
url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&hourly=temperature_2m"
    "&forecast_days=3"
)
data = requests.get(url).json()
temps = data["hourly"]["temperature_2m"]

alert_below = False
alert_above = False

for t1, t2 in zip(temps, temps[1:]):
    if t1 >= THRESHOLD and t2 < THRESHOLD:
        alert_below = True
    if t1 < THRESHOLD and t2 >= THRESHOLD:
        alert_above = True

if not (alert_below or alert_above):
    exit()

# ===== EMAIL =====
msg = EmailMessage()
msg["Subject"] = "Alerte température – Condrieu"
msg["From"] = EMAIL_FROM
msg["To"] = EMAIL_TO

body = "Alerte météo à Condrieu :\n\n"
if alert_below:
    body += "- Passage sous 1°C prévu\n"
if alert_above:
    body += "- Remontée au-dessus de 1°C prévue\n"

msg.set_content(body)

with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    server.send_message(msg)

STATE_FILE.write_text(TODAY)
