# imghdr.py — Python 3.13'te kaldırılan modül için basit yedek
# PTB 13.x içindeki `telegram.files.inputfile` -> imghdr.what() çağrısını karşılar.

from PIL import Image

def what(file, h=None):
    try:
        img = Image.open(file)
        fmt = (img.format or "").lower()
        # Python'un eski imghdr isimleriyle eşle
        mapping = {
            "jpeg": "jpeg",
            "jpg": "jpeg",
            "png": "png",
            "gif": "gif",
            "bmp": "bmp",
            "tiff": "tiff",
            "webp": "webp",
        }
        return mapping.get(fmt)
    except Exception:
        return None
