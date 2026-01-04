import requests
import datetime
import smtplib
import os
from email.message import EmailMessage
from pathlib import Path

# ===== CONFIG =====
LAT = 45.46
LON = 4.77
THRESHOLD = 1.0

EMAIL_TO = os.environ["EMAIL_TO"]
EMAIL_FROM = os.environ["EMAIL_FROM"]
SMTP_SERVER = os.environ["SMTP_SERVER"]
SMTP_PORT = int(os.environ["SMTP_PORT"])
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]

STATE_FILE = Path("last_alert.txt")

# ===== DATE / HEURE =====
now = datetime.datetime.now(datetime.timezone.utc)

# ===== METEO =====
url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={LAT}&longitude={LON}"
    "&hourly=temperature_2m"
    "&forecast_days=4"
    "&timezone=Europe/Paris"
)

data = requests.get(url).json()
times = data["hourly"]["time"]
temps = data["hourly"]["temperature_2m"]

# ===== EXTRAIRE LES NUITS =====
nights = {}  # {date: [temps]}
for t, temp in zip(times, temps):
    dt = datetime.datetime.fromisoformat(t)
    hour = dt.hour
    date = dt.date()

    # nuit = 22h → 23h OU 0h → 6h
    if hour >= 22:
        nights.setdefault(date, []).append(temp)
    elif hour <= 6:
        nights.setdefault(date - datetime.timedelta(days=1), []).append(temp)

# Trier les nuits
sorted_nights = sorted(nights.items())

# ===== ANALYSE =====
next_night_temps = sorted_nights[0][1]
next_night_below = any(t < THRESHOLD for t in next_night_temps)

next_3_nights = sorted_nights[:3]
all_3_nights_safe = all(
    all(t >= THRESHOLD for t in temps)
    for _, temps in next_3_nights
)

# ===== DERNIER ETAT =====
last_alert = STATE_FILE.read_text().strip() if STATE_FILE.exists() else None

alert_type = None

if next_night_below:
    alert_type = "A"
elif all_3_nights_safe:
    alert_type = "B"

# Rien à envoyer
if alert_type is None or alert_type == last_alert:
    exit()

# ===== EMAIL =====
msg = EmailMessage()

if alert_type == "A":
    msg["Subject"] = "Alerte gel – Condrieu"
    msg.set_content("Brancher prise chauffe-eau solaire")
else:
    msg["Subject"] = "Debrancher prise chauffe-eau solaire"
    msg.set_content("B")

msg["From"] = EMAIL_FROM
msg["To"] = EMAIL_TO

with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(SMTP_USER, SMTP_PASS)
    server.send_message(msg)

STATE_FILE.write_text(alert_type)
