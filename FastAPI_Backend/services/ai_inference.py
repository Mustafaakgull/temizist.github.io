import random
import requests

from core.config import settings


async def process_image_mock(image_bytes: bytes) -> str:
    # Gerçek senaryoda bu fonksiyon görseli Yerel Yapay Zeka Çıkarım Sunucusuna gönderir.
    # Eğer Yerel AI Sunucusu aktif ise gerçek TFLite tahminini kullanır.
    # Çevrimdışı ise sistemin test edilebilmesi için mock (temsili) veri döner.
    try:
        # Local AI sunucusuna görseli POST et
        # Yapay zekanın ne gördüğünü bizim de görebilmemiz için fotoğrafı kaydet
        with open("last_capture.jpg", "wb") as f:
            f.write(image_bytes)
            
        url = f"{settings.AI_SERVER_URL.rstrip('/')}/predict"
        files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
        response = requests.post(url, files=files, timeout=30.0)
        
        if response.status_code == 200:
            res_json = response.json()
            if res_json.get("success"):
                predicted_class = res_json.get("class")
                print(f"[AI SERVER] Gerçek TFLite tespiti: {predicted_class} (Güven: {res_json.get('confidence')})")
                return predicted_class
    except Exception as e:
        print(f"[AI SERVER OFFLINE] Yerel AI sunucusuna bağlanılamadı, mock tahmine geçiliyor. Detay: {e}")
        
    predictions = ["plastic", "paper", "reject"]
    # %60 plastik, %30 kağıt, %10 reject
    return random.choices(predictions, weights=[60, 30, 10])[0]
