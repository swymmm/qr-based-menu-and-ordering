import qrcode
import os

BASE_URL = "http://192.168.137.1:5000/"   # update to your laptop IP or domain

os.makedirs("static/qr", exist_ok=True)

# Example: 10 tables (no outlet preselected)
for table_no in range(1, 11):
    url = f"{BASE_URL}?table={table_no}"
    img = qrcode.make(url)
    img.save(f"static/qr/table_{table_no}.png")

print("✅ QR codes generated in static/qr/")
