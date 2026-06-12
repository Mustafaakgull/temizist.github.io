import cv2
import os
import time
from datetime import datetime
import sys

# Pi üzerindeki veri seti ana dizini
DATASET_DIR = "/home/temizist/TemizIST/dataset"

def main():
    # Sınıf adının argüman olarak verilip verilmediğini kontrol et
    if len(sys.argv) < 2:
        print("Kullanım: python3 pi_auto_capture.py <sinif_adi>")
        print("Örnek sınıflar: plastic, paper, glass, metal, trash")
        print("Örnek komut: python3 pi_auto_capture.py plastic")
        return

    target_class = sys.argv[1].lower()
    target_dir = os.path.join(DATASET_DIR, target_class)
    
    # Klasör yoksa otomatik oluştur
    os.makedirs(target_dir, exist_ok=True)
    
    print("=== PI Headless Veri Toplama ===")
    print(f"Seçilen Sınıf: {target_class}")
    print(f"Hedef Klasör: {target_dir}")
    print("\n[BİLGİ] Her ENTER'a bastığınızda 1 fotoğraf çekilecek.")
    print("[BİLGİ] İşlemi durdurmak için 'q' yazıp ENTER'a basın...\n")
    
    # Kamerayı başlat (Pi'de genelde 0'dır)
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("HATA: Kamera açılamadı! (Başka bir script kamerayı kullanıyor olabilir)")
        return

    # Kameranın ışık/odak ayarı için bekle
    time.sleep(2)
    count = 0
    
    try:
        while True:
            cmd = input(f"[{count}] Çekmek için ENTER (Çıkış: q) > ")
            if cmd.lower() == 'q':
                break
                
            # ÖNEMLİ: Siz beklerken kameranın önbelleğinde (buffer) eski kareler birikir.
            # Taze bir görüntü almak için arabellekteki son 5 kareyi hızlıca okuyup çöpe atıyoruz.
            for _ in range(5):
                cap.read()
                
            ret, frame = cap.read()
            if not ret:
                print("HATA: Kameradan kare alınamadı!")
                continue
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = f"{target_class}_{timestamp}.jpg"
            filepath = os.path.join(target_dir, filename)
            
            # Pi üzerinde Linux çalıştığı için Türkçe karakter sorunu yoktur, cv2.imwrite güvenlidir
            cv2.imwrite(filepath, frame)
            count += 1
            print(f" -> KAYDEDİLDİ: {filename}")
            
    except KeyboardInterrupt:
        print("\nCTRL+C algılandı. İşlem durduruluyor...")
    finally:
        cap.release()
        print(f"\nİşlem tamamlandı. Toplam {count} adet yeni '{target_class}' fotoğrafı eklendi.")

if __name__ == "__main__":
    main()
