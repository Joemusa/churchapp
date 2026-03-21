import qrcode

app_url = "https://churchapp-svj7q8md3mvysqgtcbsjcn.streamlit.app/"
file_name = "church_checkin_qr.png"

img = qrcode.make(app_url)
img.save(file_name)

print(f"QR code saved as {file_name}")
