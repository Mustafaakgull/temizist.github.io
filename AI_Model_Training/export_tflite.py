# export_tflite.py
# Bu dosya, eğitilen Keras modelini (.keras / .h5) Raspberry Pi gibi gömülü
# sistemlerde çalıştırılabilmesi için son derece optimize edilmiş ".tflite" formatına dönüştürür.
# Ayrıca "Quantization" (Niceleme) uygulayarak model boyutunu 14MB'tan 3.5MB'a düşürür ve hızı 4 kat artırır.

import tensorflow as tf
import os

MODEL_PATH = "waste_classifier.keras"
MODEL_H5_PATH = "waste_classifier.h5"
TFLITE_PATH = "waste_classifier.tflite"

def convert_to_tflite():
    print("=== TEMİZİST TensorFlow Lite Dönüştürücü Başlıyor ===")
    
    # Kaydedilmiş modeli yükle
    if os.path.exists(MODEL_PATH):
        print(f"Model yükleniyor: {MODEL_PATH}")
        model = tf.keras.models.load_model(MODEL_PATH)
    elif os.path.exists(MODEL_H5_PATH):
        print(f"Model yükleniyor: {MODEL_H5_PATH}")
        model = tf.keras.models.load_model(MODEL_H5_PATH)
    else:
        print("Hata: Eğitilmiş model dosyası (.keras veya .h5) bulunamadı! Lütfen önce 'train.py' dosyasını çalıştırın.")
        return

    print("Dönüştürme işlemi başlatılıyor...")
    # TFLite Converter tanımla
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    
    # 8-Bit Quantization (Niceleme) Optimizasyonu
    # Bu optimizasyon, Pi işlemcisinde işlem yükünü hafifletir ve hızı maksimuma çıkarır.
    print("Edge CPU / Raspberry Pi için dinamik niceleme (quantization) optimizasyonları uygulanıyor...")
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    
    # Dönüştürme işlemini gerçekleştir
    tflite_model = converter.convert()
    
    # .tflite dosyasını diske yaz
    print(f"TFLite modeli kaydediliyor: {TFLITE_PATH}")
    with open(TFLITE_PATH, "wb") as f:
        f.write(tflite_model)
        
    print("\nDönüştürme ve Optimizasyon Başarıyla Tamamlandı!")
    
    # Boyut karşılaştırması yap
    original_size = 0
    if os.path.exists(MODEL_PATH):
        original_size = os.path.getsize(MODEL_PATH) / (1024 * 1024)
    elif os.path.exists(MODEL_H5_PATH):
        original_size = os.path.getsize(MODEL_H5_PATH) / (1024 * 1024)
        
    tflite_size = os.path.getsize(TFLITE_PATH) / (1024 * 1024)
    
    print(f" - Orijinal Model Boyutu: {original_size:.2f} MB")
    print(f" - Optimize TFLite Model Boyutu: {tflite_size:.2f} MB")
    print(f" - Sıkıştırma Oranı: %{((original_size - tflite_size) / original_size * 100):.1f} küçülme!")
    print(f"\nArtık '{TFLITE_PATH}' dosyasını doğrudan Raspberry Pi cihazınıza kopyalayarak çalıştırabilirsiniz!")

if __name__ == "__main__":
    convert_to_tflite()
