import sys
import os
import qrcode
sys.path.append(os.getcwd())

try:
    qr = qrcode.QRCode()
    qr.add_data("test")
    img = qr.make_image(fill_color="black", back_color="white")
    if hasattr(img, '_img'):
        print(f"Type of _img: {type(img._img)}")
    else:
        print("No _img attribute")
except Exception as e:
    import traceback
    traceback.print_exc()
