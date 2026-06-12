# train.py
# TEMİZİST Yapay Zeka Model Eğitim Scripti
# Bu script, MobileNetV2 transfer learning (aktarımlı öğrenme) kullanarak 
# plastik, kağıt/karton ve diğer atık türlerini yüksek doğrulukla sınıflandırır.

import os
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras import layers, models
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
import matplotlib.pyplot as plt

# Hiperparametreler ve Konfigürasyon
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
EPOCHS = 15
DATASET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dataset")
MODEL_NAME = "waste_classifier.keras"
MODEL_H5_NAME = "waste_classifier.h5"

def train_model():
    print("=== TEMİZİST Yapay Zeka Model Eğitimi Başlıyor ===")
    
    if not os.path.exists(DATASET_DIR) or len(os.listdir(DATASET_DIR)) == 0:
        print(f"Hata: '{DATASET_DIR}' klasörü bulunamadı veya boş! Lütfen önce 'download_dataset.py' dosyasını çalıştırın.")
        return

    # Sınıf İsimlerini Listele
    classes = sorted(os.listdir(DATASET_DIR))
    num_classes = len(classes)
    print(f"Tespit edilen atık sınıfları: {classes} (Toplam {num_classes} sınıf)")

    # Veri Artırımı (Data Augmentation) ve Ön İşleme
    # Bu adımlar, modelin akıllı kutudaki farklı ışık/açı durumlarında stabil çalışmasını sağlar.
    train_datagen = ImageDataGenerator(
        rescale=1./255,               # Pikselleri 0-1 arasına ölçekle
        rotation_range=30,            # Görselleri rastgele 30 dereceye kadar döndür
        width_shift_range=0.2,        # Yatay kaydır
        height_shift_range=0.2,       # Dikey kaydır
        shear_range=0.2,              # Eğrilt
        zoom_range=0.2,               # Rastgele yakınlaştır
        horizontal_flip=True,         # Rastgele yatay olarak ters çevir
        validation_split=0.2          # %20 validation (doğrulama) payı ayır
    )

    print("\nGörseller yükleniyor ve ön işlemeden geçiriliyor...")
    
    # Eğitim Veri Seti Jeneratörü
    train_generator = train_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='training',
        shuffle=True
    )

    # Doğrulama Veri Seti Jeneratörü
    val_generator = train_datagen.flow_from_directory(
        DATASET_DIR,
        target_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        subset='validation',
        shuffle=False
    )

    # Model Mimarisi: Mobil ve Hafif MobileNetV2 (ImageNet ağırlıklarıyla hazır)
    print("\nPre-trained MobileNetV2 taban modeli yükleniyor...")
    base_model = MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,            # Üst tam bağlantılı katmanları (klasik sınıfları) alma
        weights='imagenet'            # Hazır ImageNet ağırlıklarını yükle
    )
    
    # Taban modelin ağırlıklarını dondur (hazır özellikleri koru, eğitme)
    base_model.trainable = False

    # Yeni Sınıflandırma Katmanlarının Eklenmesi (Derin ve Kararlı Mimari)
    model = models.Sequential([
        base_model,
        layers.GlobalAveragePooling2D(),
        layers.Dense(256, activation='relu'),
        layers.BatchNormalization(),          # Eğitim stabilitesi için Batch Normalization ekledik
        layers.Dropout(0.4),                  # Ezberlemeyi önlemek için daha güçlü dropout
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation='softmax')
    ])

    model.compile(
        optimizer='adam',
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    print("\nModel Özeti:")
    model.summary()

    # Akıllı Geri Çağırma (Callbacks) Mekanizmaları
    callbacks = [
        # Eğer validation loss 3 epoch boyunca iyileşmezse eğitimi erken sonlandır
        EarlyStopping(monitor='val_loss', patience=3, restore_best_weights=True),
        # En iyi ağırlıklara sahip modeli otomatik kaydet
        ModelCheckpoint(MODEL_NAME, monitor='val_accuracy', save_best_only=True, mode='max', verbose=1)
    ]

    # Modeli Eğit
    print(f"\nEğitim Başlıyor... ({EPOCHS} Epoch planlandı)")
    history = model.fit(
        train_generator,
        steps_per_epoch=train_generator.samples // BATCH_SIZE,
        epochs=EPOCHS,
        validation_data=val_generator,
        validation_steps=val_generator.samples // BATCH_SIZE,
        callbacks=callbacks
    )

    # Modeli Farklı Formatlarda Kaydet
    print("\nModel dosyaları kaydediliyor...")
    model.save(MODEL_NAME) # .keras formatı
    model.save(MODEL_H5_NAME) # Klasik .h5 formatı (IoT/Pi uyumluluğu için garanti)
    print(f"Başarılı! Model '{MODEL_NAME}' ve '{MODEL_H5_NAME}' olarak kaydedildi.")

    # Eğitim Grafiğini Kaydet
    try:
        plt.figure(figsize=(12, 4))
        plt.subplot(1, 2, 1)
        plt.plot(history.history['accuracy'], label='Eğitim Doğruluğu')
        plt.plot(history.history['val_accuracy'], label='Doğrulama Doğruluğu')
        plt.title('Model Doğruluğu')
        plt.xlabel('Epoch')
        plt.ylabel('Doğruluk')
        plt.legend()

        plt.subplot(1, 2, 2)
        plt.plot(history.history['loss'], label='Eğitim Kaybı')
        plt.plot(history.history['val_loss'], label='Doğrulama Kaybı')
        plt.title('Model Kaybı')
        plt.xlabel('Epoch')
        plt.ylabel('Kayıp')
        plt.legend()
        
        plt.savefig('training_history.png')
        print("Eğitim grafiği 'training_history.png' olarak başarıyla kaydedildi.")
    except Exception as e:
        print(f"Grafik kaydedilirken hata oluştu (matplotlib yüklü olmayabilir): {e}")

    print("\nTebrikler! Model eğitim süreci tamamlandı. Sırada '.tflite' dönüştürme adımı var.")

if __name__ == "__main__":
    train_model()
