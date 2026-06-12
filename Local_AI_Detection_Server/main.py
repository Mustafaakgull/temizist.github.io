# main.py
# TEMİZİST Yerel Yapay Zeka Sunucusu - FastAPI Uygulaması
# Bu sunucu local ağda çalışarak Raspberry Pi veya merkezi sunucudan gelen
# görselleri anlık olarak eğitilmiş TFLite modelimizle sınıflandırır.

import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from classifier import WasteClassifier

app = FastAPI(
    title="TEMİZİST Yerel Yapay Zeka Algılama Sunucusu",
    description="Atık görsellerini MobileNetV2 TFLite modeliyle sınıflandıran yerel AI çıkarım mikroservisi.",
    version="1.0.0"
)

# CORS (Kökenler Arası Kaynak Paylaşımı) Ayarları - Ağdaki cihazların erişebilmesi için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model yükleme
try:
    classifier = WasteClassifier("waste_classifier.tflite")
except Exception as e:
    print(f"\n[HATA] TFLite modeli yüklenirken sorun oluştu: {e}")
    classifier = None

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "TEMİZİST Yerel Yapay Zeka Algılama Sunucusu",
        "model_loaded": classifier is not None,
        "classes": classifier.classes if classifier else []
    }

@app.get("/health")
def health_check():
    if classifier is None:
        raise HTTPException(status_code=503, detail="Yapay Zeka Modeli Yüklenemedi!")
    return {"status": "healthy", "model": "waste_classifier.tflite"}

@app.post("/predict")
async def predict_waste(file: UploadFile = File(...)):
    """
    Form-data olarak gönderilen görseli TFLite modeliyle analiz eder.
    Sınıfı ('paper' veya 'plastic') ve güven (confidence) oranını döner.
    """
    if classifier is None:
        raise HTTPException(status_code=503, detail="Model yüklü değil veya sunucuda hata oluştu!")
    
    # Görsel uzantısı kontrolü
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Hata: Yüklenen dosya geçerli bir görsel değil.")

    try:
        # Görsel verisini oku ve Pillow Image nesnesine aktar
        image_bytes = await file.read()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Çıkarım işlemini gerçekleştir
        predicted_class, confidence = classifier.predict(image)
        
        # Türkçe açıklayıcı mesaj üret
        if predicted_class == "plastic":
            message = "Plastik atık (şişe, pet vb.) başarıyla tespit edildi."
        elif predicted_class == "paper":
            message = "Kağıt/Karton atık başarıyla tespit edildi."
        elif predicted_class == "glass":
            message = "Cam atık (şişe, kavanoz vb.) tespit edildi. Geri dönüşüm için reddedildi."
        elif predicted_class == "metal":
            message = "Metal atık (teneke kutu vb.) tespit edildi. Geri dönüşüm için reddedildi."
        elif predicted_class == "trash":
            message = "Geri dönüştürülemeyen genel çöp/atık tespit edildi. Reddedildi."
        else:
            message = "Atık türü tanınamadı."

        return {
            "success": True,
            "class": predicted_class,
            "confidence": round(confidence, 4),
            "message": message
        }
    except Exception as e:
        print(f"[PREDICT ERROR] Hata oluştu: {e}")
        raise HTTPException(status_code=500, detail=f"Görsel işlenirken hata oluştu: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Local ağdaki diğer cihazların (örn. Raspberry Pi) sunucuya erişebilmesi için 0.0.0.0 olarak başlatalım
    uvicorn.run("main:app", host="0.0.0.0", port=9000, reload=True)
