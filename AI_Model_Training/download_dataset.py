# download_dataset.py
# Bu dosya, model eğitimi için kullanılacak olan endüstri standardı "TrashNet" veri setini
# kagglehub kütüphanesini kullanarak otomatik olarak indirir, kağıt ve karton sınıflarını birleştirir
# ve "dataset/" klasörüne çıkartır.

import os
import shutil
import kagglehub

EXTRACT_DIR = "dataset"
DATASET_ID = "feyzazkefe/trashnet"

def download_and_extract():
    print("=== TEMİZİST Yapay Zeka Veri Seti Hazırlayıcı (KaggleHub) ===")
    
    # Hedef klasörü temizle veya oluştur
    if os.path.exists(EXTRACT_DIR):
        print(f"'{EXTRACT_DIR}' klasörü temizleniyor...")
        shutil.rmtree(EXTRACT_DIR)
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    
    print(f"Kaggle üzerinden '{DATASET_ID}' veri seti indiriliyor...")
    print("Lütfen bekleyin (KaggleHub indirmeyi otomatik önbelleğe alır ve hızlıdır)...")
    
    try:
        # kagglehub kullanarak veri setini indir
        download_path = kagglehub.dataset_download(DATASET_ID)
        print(f"İndirme tamamlandı! Önbellek konumu: {download_path}")
        
        # İndirilen klasörün içeriğini tara. Bazen dosyalar doğrudan kök dizinde, 
        # bazen de 'dataset-original' veya 'dataset-resized' alt klasörlerindedir.
        source_dir = download_path
        
        # Eğer alt klasörler varsa tespit et
        subfolders = [f for f in os.listdir(download_path) if os.path.isdir(os.path.join(download_path, f))]
        for folder in subfolders:
            if "resized" in folder.lower() or "original" in folder.lower() or "dataset" in folder.lower():
                candidate_path = os.path.join(download_path, folder)
                # İçinde 'plastic' veya 'paper' gibi sınıflar var mı kontrol et
                inner_folders = [f for f in os.listdir(candidate_path) if os.path.isdir(os.path.join(candidate_path, f))]
                if "plastic" in inner_folders or "paper" in inner_folders:
                    source_dir = candidate_path
                    break
        
        print(f"Kaynak sınıf klasörleri tespit edildi: {source_dir}")
        classes_found = [f for f in os.listdir(source_dir) if os.path.isdir(os.path.join(source_dir, f))]
        print(f"Veri setindeki sınıflar: {classes_found}")
        
        # 1. Dosyaları yerel proje 'dataset' klasörüne kopyala
        print("\nGörseller projenin yerel klasörüne kopyalanıyor...")
        for c in classes_found:
            src_class_path = os.path.join(source_dir, c)
            dst_class_path = os.path.join(EXTRACT_DIR, c)
            shutil.copytree(src_class_path, dst_class_path)
            
        # 2. Kağıt ve Karton klasörlerini birleştir
        paper_dir = os.path.join(EXTRACT_DIR, "paper")
        cardboard_dir = os.path.join(EXTRACT_DIR, "cardboard")
        
        if os.path.exists(cardboard_dir) and os.path.exists(paper_dir):
            print("\n - 'cardboard' (karton) görselleri 'paper' (kağıt) sınıfıyla birleştiriliyor...")
            for img in os.listdir(cardboard_dir):
                src = os.path.join(cardboard_dir, img)
                dst = os.path.join(paper_dir, f"cardboard_{img}")
                shutil.move(src, dst)
            shutil.rmtree(cardboard_dir)
            print(" - Kağıt ve Karton başarıyla tek bir 'paper' sınıfı altında toplandı.")
            
        # Klasör yapısını son olarak doğrula
        final_classes = os.listdir(EXTRACT_DIR)
        print(f"\nGüncel Veri Seti Yapısı ve Sınıfları: {final_classes}")
        for s in final_classes:
            subdir_path = os.path.join(EXTRACT_DIR, s)
            if os.path.isdir(subdir_path):
                print(f" - {s}: {len(os.listdir(subdir_path))} adet görsel")
                
        print("\nVeri seti başarıyla hazırlandı! Artık 'train.py' dosyasını çalıştırabilirsiniz.")
                
    except Exception as e:
        print(f"\nHata: İşlemler gerçekleştirilirken sorun oluştu. Detay: {e}")

if __name__ == "__main__":
    download_and_extract()
