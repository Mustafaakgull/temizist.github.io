# TEMİZİST Yerel Yapay Zeka Çıkarım Sunucusu

Bu proje, akıllı geri dönüşüm kutusunun (Raspberry Pi) kamerası tarafından çekilen atık fotoğraflarını anlık olarak sınıflandıran hafif bir **FastAPI mikroservisidir**. 

Ağda çalışan bu sunucu, ana web backend sunucusunun (Docker/VPS) yapay zeka yükünü hafifletmek için tasarlanmıştır. Bu sayede ana sunucuya devasa TensorFlow kütüphanelerini kurmak gerekmez ve çıkarım işlemleri local ağda milisaniyeler seviyesinde gerçekleşir.

## Özellikler
*   **MobileNetV2 Transfer Learning:** Plastik şişe ve Kağıt/Karton sınıfları için özel eğitilmiş model.
*   **TFLite Optimizasyonu:** Model boyutu Niceleme (Quantization) ile 11MB'tan 2.6MB'a düşürülmüştür ve CPU üzerinde 4 kat daha hızlı çalışır.
*   **Çift Platform Desteği:** 
    *   PC üzerinde standart **TensorFlow** ile çalışır.
    *   Raspberry Pi üzerinde hafif **tflite-runtime** ile çalışarak RAM ve işlemci tüketimini sıfıra indirir.

---

## Kurulum ve Çalıştırma

### 1. Kütüphaneleri Yükleyin
Eğer projenin FastAPI sanal ortamını kullanıyorsanız gerekli paketler zaten kuruludur. Yeni bir ortamda kurmak isterseniz:

```bash
# PC / Geliştirme Ortamı İçin:
pip install fastapi uvicorn pillow numpy tensorflow

# Raspberry Pi / Gömülü Sistem İçin (Çok daha hafiftir):
pip install fastapi uvicorn pillow numpy tflite-runtime
```

### 2. Sunucuyu Başlatın
Sunucuyu başlatmak için `main.py` dosyasını çalıştırın:

```bash
python main.py
```

Sunucu varsayılan olarak local ağdaki tüm cihazların erişebilmesi için `0.0.0.0` IP'sini dinleyecek şekilde **9000** portunda başlar:
`http://localhost:9000`

---

## API Uç Noktaları (Endpoints)

### 1. Sunucu Durumu (Health Check)
Sunucunun ve yapay zeka modelinin düzgün yüklenip yüklenmediğini kontrol eder.

*   **Uç Nokta:** `GET /health`
*   **Yanıt:**
    ```json
    {
      "status": "healthy",
      "model": "waste_classifier.tflite"
    }
    ```

### 2. Atık Tahmin Etme (Predict)
Gönderilen görseli TFLite modeliyle analiz eder.

*   **Uç Nokta:** `POST /predict`
*   **İstek Formatı:** `multipart/form-data`
    *   `file`: (Görsel dosyası - jpeg, png vb.)
*   **Yanıt (Plastik):**
    ```json
    {
      "success": true,
      "class": "plastic",
      "confidence": 0.9854,
      "message": "Plastik atık (şişe, pet vb.) başarıyla tespit edildi."
    }
    ```
*   **Yanıt (Kağıt):**
    ```json
    {
      "success": true,
      "class": "paper",
      "confidence": 0.9642,
      "message": "Kağıt/Karton atık başarıyla tespit edildi."
    }
    ```
