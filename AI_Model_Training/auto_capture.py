import cv2
import os
import time
from datetime import datetime

# Veri seti ana dizini
DATASET_DIR = r"c:\Users\gokha\Masaüstü\Graduation Project\dataset"

def main():
    print("=== TEMİZİST Otomatik Veri Toplama Aracı ===")
    
    # Sınıfları listele
    classes = [d for d in os.listdir(DATASET_DIR) if os.path.isdir(os.path.join(DATASET_DIR, d))]
    
    if not classes:
        print("Hata: Dataset klasöründe sınıf alt klasörleri bulunamadı!")
        return

    print("\nMevcut Sınıflar:")
    for i, c in enumerate(classes):
        print(f"{i + 1}. {c}")
        
    class_idx = int(input("\nHangi sınıf için fotoğraf çekeceksiniz? (Numara girin): ")) - 1
    
    if class_idx < 0 or class_idx >= len(classes):
        print("Geçersiz seçim!")
        return
        
    target_class = classes[class_idx]
    target_dir = os.path.join(DATASET_DIR, target_class)
    
    print(f"\nSeçilen Sınıf: {target_class}")
    print(f"Hedef Klasör: {target_dir}")
    print("\nKamera açılıyor... Çıkmak için ekrandayken 'q' tuşuna basın.")
    
    # Kamerayı başlat (0 genellikle dahili web kamerasıdır)
    cap = cv2.VideoCapture(1)
    
    if not cap.isOpened():
        print("Hata: Kamera açılamadı!")
        return

    # Kameranın biraz ısınmasını bekle
    time.sleep(2)
    
    count = 0
    last_capture_time = time.time()
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Kameradan görüntü alınamadı!")
                break
                
            # Ekranda gösterilecek kopyayı oluştur
            display_frame = frame.copy()
            
            # Bilgileri ekrana yaz
            cv2.putText(display_frame, f"Sinif: {target_class}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Cekilen: {count}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(display_frame, "Cekmek icin 'ENTER' veya 'SPACE'", (10, display_frame.shape[0] - 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
            cv2.putText(display_frame, "Cikmak icin 'q'", (10, display_frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            cv2.imshow("Manuel Veri Toplama", display_frame)
            
            key = cv2.waitKey(1) & 0xFF
            
            # Enter (13) veya Space (32) tuşuna basılırsa fotoğrafı kaydet
            if key == 13 or key == 32:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
                filename = f"{target_class}_{timestamp}.jpg"
                filepath = os.path.join(target_dir, filename)
                
                # OpenCV Türkçe yollarda cv2.imwrite ile çökmeden sessizce başarısız olur.
                # Bu yüzden imencode ve numpy tofile kullanıyoruz.
                is_success, im_buf_arr = cv2.imencode(".jpg", frame)
                if is_success:
                    im_buf_arr.tofile(filepath)
                    count += 1
                    print(f"Kaydedildi: {filename} (Toplam: {count})")
                else:
                    print(f"HATA: {filename} kaydedilemedi!")
                
                # Çekildiğini belli etmek için ekranı anlık yeşil yap
                cv2.rectangle(display_frame, (0, 0), (display_frame.shape[1], display_frame.shape[0]), (0, 255, 0), 20)
                cv2.imshow("Manuel Veri Toplama", display_frame)
                cv2.waitKey(100) # 100ms yeşil kalsın
                
            # 'q' tuşuna basılırsa çık
            elif key == ord('q'):
                print("\nKullanıcı tarafından durduruldu.")
                break
                
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print(f"\nİşlem tamamlandı. Toplam {count} adet yeni '{target_class}' fotoğrafı eklendi.")

if __name__ == "__main__":
    main()
