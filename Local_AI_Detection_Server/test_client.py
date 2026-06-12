# test_client.py
# TEMİZİST Yapay Zeka Test İstemcisi
# Bu betik, belirtilen bir test görselini yerel yapay zeka sunucusuna (port 9000)
# göndererek modelin sınıflandırma doğruluğunu anlık olarak test etmenizi sağlar.

import sys
import os
import requests

# CLI Renk Kodları
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"

URL = "http://127.0.0.1:9000/predict"

def test_prediction(image_path):
    print(f"\n{BOLD}=== TEMİZİST Yapay Zeka Test Süreci ==={RESET}")
    
    if not os.path.exists(image_path):
        print(f"{RED}Hata: '{image_path}' yolundaki görsel dosyası bulunamadı!{RESET}")
        print("Lütfen test etmek istediğiniz görselin yolunu doğru girin.")
        return

    print(f"Görsel analiz için yükleniyor: {image_path}")
    
    try:
        # Görseli oku ve sunucuya gönder
        with open(image_path, "rb") as img_file:
            files = {"file": (os.path.basename(image_path), img_file, "image/jpeg")}
            print("Yerel Yapay Zeka Sunucusuna (Port 9000) gönderiliyor...")
            
            response = requests.post(URL, files=files, timeout=5.0)
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    predicted_class = result.get("class")
                    confidence = result.get("confidence")
                    message = result.get("message")
                    
                    # Sonuçları renkli ve okunaklı yazdır
                    color = GREEN if predicted_class == "plastic" else YELLOW
                    print(f"\n{BOLD}Analiz Tamamlandı!{RESET}")
                    print(f" - Tahmin Edilen Sınıf: {color}{BOLD}{predicted_class.upper()}{RESET}")
                    print(f" - Güven/Doğruluk Oranı: {GREEN}{confidence * 100:.2f}%{RESET}")
                    print(f" - Sunucu Mesajı: {CYAN}{message}{RESET}\n")
                else:
                    print(f"{RED}Sunucu Başarısız Yanıt Döndü: {result.get('message')}{RESET}")
            else:
                print(f"{RED}Hata: Sunucu hata kodu döndürdü ({response.status_code}): {response.text}{RESET}")
                
    except requests.exceptions.ConnectionError:
        print(f"{RED}Hata: Yerel Yapay Zeka Sunucusuna bağlanılamadı!{RESET}")
        print(f"{YELLOW}Lütfen sunucuyu başlattığınızdan emin olun: {RESET}python main.py")
    except Exception as e:
        print(f"{RED}Beklenmedik bir hata oluştu: {e}{RESET}")

if __name__ == "__main__":
    # Eğer komut satırından görsel yolu verilmediyse veri setindeki bir görseli örnek seçelim
    if len(sys.argv) > 1:
        test_image = sys.argv[1]
    else:
        # Veri setimizden örnek bir plastik resmini varsayılan yapalım
        dataset_dir = os.path.join("..", "dataset")
        default_img = ""
        
        if os.path.exists(dataset_dir):
            # İlk bulduğun plastik görselini test için kullan
            plastic_dir = os.path.join(dataset_dir, "plastic")
            if os.path.exists(plastic_dir) and len(os.listdir(plastic_dir)) > 0:
                default_img = os.path.join(plastic_dir, os.listdir(plastic_dir)[0])
        
        if default_img:
            test_image = default_img
            print(f"{YELLOW}Bilgi: Görsel belirtilmedi, otomatik olarak veri setindeki örnek görsel seçildi.{RESET}")
        else:
            # Fallback
            test_image = "test_image.jpg"
            
    test_prediction(test_image)
