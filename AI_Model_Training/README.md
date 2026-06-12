# TEMİZİST Yapay Zeka Model Eğitim Kılavuzu

Bu dizin, akıllı geri dönüşüm kutusuna atılan atıkları (Plastik Şişe ve Kağıt/Karton) yüksek hız ve doğrulukla tespit edecek derin öğrenme modelini eğitmek ve optimize etmek için geliştirilmiştir.

---

## Proje Yapısı

* **`download_dataset.py`**: Endüstri standardı açık kaynaklı **TrashNet** atık sınıflandırma veri setini otomatik olarak indirir, **karton ve kağıt kategorilerini tek bir sınıf altında birleştirir** ve kullanılmayan diğer atık sınıflarını (cam, metal vb.) temizler.
* **`train.py`**: **MobileNetV2** tabanlı derin öğrenme transfer learning modelini eğitir. Eğitim sonunda en iyi modeli `.keras` ve `.h5` formatlarında kaydeder.
* **`export_tflite.py`**: Eğitilen modeli Raspberry Pi gibi cihazlarda çalışacak şekilde **TensorFlow Lite (.tflite)** formatına dönüştürür ve %75 oranında sıkıştırır (14MB -> 3.5MB).

---

## Kurulum ve Hazırlık

Eğitim yapacağınız bilgisayarda (harici ekran kartınız varsa GPU içeren bir PC önerilir, yoksa standart CPU ile de birkaç dakikada tamamlanacaktır) gerekli kütüphaneleri yükleyin:

```bash
pip install tensorflow pillow numpy matplotlib
```

---

## Adım Adım Eğitim Süreci

### 1. Adım: Veri Setini İndirin ve Birleştirin
İlk olarak veri setini otomatik indirmek ve düzenlemek için scripti çalıştırın:
```bash
python download_dataset.py
```
Bu komut internetten veri setini indirip `dataset/` adında bir klasör oluşturur ve aşağıdaki gibi **tam olarak 2 sınıf (Binary Classification)** barındıracak şekilde düzenler:
* `paper` (Kağıt ve Karton görselleri bir arada)
* `plastic` (Plastik şişe görselleri)

### 2. Adım: Modeli Eğitin
Modelin eğitilmesini başlatın:
```bash
python train.py
```
* **Ön İşleme:** Görseller 224x224 boyutuna getirilerek yatay çevirme, döndürme ve yakınlaştırma gibi veri artırımı (Data Augmentation) filtrelerinden geçirilir. Bu, kutu içindeki farklı açıları simüle eder.
* **Transfer Learning:** Google'ın edge cihazları için tasarladığı **MobileNetV2** mimarisi ImageNet ağırlıklarıyla yüklenir ve üstüne kendi atık sınıflarımız için katmanlar eklenerek eğitilir.
* **Erken Durdurma:** Model doğruluk oranı zirveye ulaştığında ezberlemeyi (overfitting) önlemek için eğitimi otomatik bitirir ve en başarılı modeli `waste_classifier.keras` ve `waste_classifier.h5` olarak kaydeder.

### 3. Adım: Raspberry Pi İçin Optimize Edin (TFLite Dönüştürme)
Modeli Raspberry Pi'nin işlemcisini yormayacak şekilde dönüştürün:
```bash
python export_tflite.py
```
Bu script, float32 ağırlık değerlerini 8-bit tam sayılara (quantization) dönüştürerek modelin boyutunu **3.5MB** seviyesine düşürür. Bu sıkıştırma Pi üzerinde işlem hızını **4 kat artırır**. İşlem sonunda **`waste_classifier.tflite`** dosyanız hazır olacaktır!

---

## Gömülü Sistemde (Raspberry Pi) Modeli Çalıştırma (Inference)

Eğittiğiniz `waste_classifier.tflite` modelini Raspberry Pi içerisine aldıktan sonra, Pi kamerası ile çekilen fotoğrafları sınıflandırmak için Pi üzerinde çalıştıracağınız örnek Python kodu:

```python
import numpy as np
from PIL import Image
import tensorflow.lite as tflite

# 1. TFLite modelini yükle ve işlemciyi ata
interpreter = tflite.Interpreter(model_path="waste_classifier.tflite")
interpreter.allocate_tensors()

# Giriş ve Çıkış katmanlarını al
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Sınıf İsimleri (Alfabetik olarak klasör sırasıyla eşleşir)
CLASS_NAMES = ['paper', 'plastic']

def classify_image(image_path):
    # Görseli oku ve 224x224 olarak yeniden boyutlandır
    img = Image.open(image_path).resize((224, 224))
    
    # Görseli numpy dizisine çevir ve normalize et (0-1 arası)
    input_data = np.expand_dims(np.array(img, dtype=np.float32) / 255.0, axis=0)
    
    # Veriyi modele besle
    interpreter.set_tensor(input_details[0]['index'], input_data)
    interpreter.invoke()
    
    # Tahmin olasılıklarını al
    predictions = interpreter.get_tensor(output_details[0]['index'])[0]
    
    # En yüksek olasılıklı sınıfı seç
    best_class_idx = np.argmax(predictions)
    detected_class = CLASS_NAMES[best_class_idx]
    confidence = predictions[best_class_idx]
    
    return detected_class, confidence

# Örnek Kullanım:
# class_name, score = classify_image("captured_waste.jpg")
# print(f"Tespit Edilen Atık: {class_name} (%{score*100:.1f} doğruluk)")
```
