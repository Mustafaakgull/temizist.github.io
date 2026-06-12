import base64
import json
from io import BytesIO
from PIL import Image
from openai import OpenAI

# API Key (Kullanıcı tarafından sağlandı)
API_KEY = ""

class WasteClassifier:
    def __init__(self, model_path=None):
        print("[INFO] OpenAI GPT-4o-mini Vision Modeli Başlatılıyor...")
        self.client = OpenAI(api_key=API_KEY)
        self.classes = ['glass', 'metal', 'paper', 'plastic', 'trash']

    def predict(self, image_pil: Image.Image):
        """
        Pillow Image nesnesi alır, Base64 formatına çevirir ve GPT-4o-mini'ye gönderir.
        """
        # Görseli RGB formatına çevir
        img = image_pil.convert('RGB')
        # Hata ayıklama için AI'nin gördüğü resmi masaüstüne kaydet
        img.save("yapay_zeka_ne_gordu.jpg")
        
        # Base64'e dönüştür (JPEG formatında)
        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        
        prompt = (
            "Sen katı atık ve geri dönüşüm sınıflandırma asistanısın. Gönderilen fotoğraftaki objeyi çok dikkatli incele.\n"
            "KURALLAR ÇOK SIKIDIR. Yanlış atıkları KESİNLİKLE kabul etmemelisin.\n"
            "1. 'plastic' SINIFI: YALNIZCA VE YALNIZCA içi boşaltılmış, su/içecek tüketimi için kullanılan belirgin 'PLASTİK ŞİŞE' (Pet şişe) formundaki objeler için geçerlidir. Bant (sellotape/koli bandı), poşet, plastik oyuncak, plastik kalem, koli bandı rulosu, mezura, plastik ambalaj gibi plastik maddeden yapılmış ama BİR ŞİŞE OLMAYAN objeleri KESİNLİKLE 'trash' (çöp) olarak işaretlemelisin! Plastik materyalden olması yetmez, kesinlikle 'şişe' formu olmalıdır!\n"
            "2. 'paper' SINIFI: Herhangi bir tür KAĞIT materyali (buruşuk kağıt, düz kağıt, karton kutu, gazete, fiş, peçete, SPİRALLİ DEFTER, kitap, karton ambalaj) ise 'paper' değerini dön. Karton, mukavva ve spiralli/telli defterler KESİNLİKLE 'paper' sınıfıdır!\n"
            "3. 'trash' SINIFI: Plastik ŞİŞE OLMAYAN ve Kağıt OLMAYAN her şey. Selobant, koli bandı rulosu, kalem, poşet, boşluk, sadece zemin vb. hepsi 'trash' olmalıdır.\n"
            "Sadece ve sadece JSON formatında yanıt dönmelisin.\n"
            "Örnek: {\"class\": \"trash\", \"confidence\": 0.99}"
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{img_base64}",
                                    "detail": "low"
                                }
                            }
                        ]
                    }
                ],
                response_format={ "type": "json_object" },
                max_tokens=50,
                temperature=0.0
            )
            
            result_json = response.choices[0].message.content
            result = json.loads(result_json)
            
            predicted_class = result.get("class", "trash").lower()
            confidence = float(result.get("confidence", 0.95))
            
            if predicted_class not in self.classes:
                predicted_class = "trash"
                
            return predicted_class, confidence
            
        except Exception as e:
            print(f"[HATA] OpenAI API Hatası: {e}")
            return "trash", 0.0
