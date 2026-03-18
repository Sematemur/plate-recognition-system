"""
YOLO Eğitim Scripti - Google Colab İçin
=========================================
Kullanım:
1. archive.zip dosyasını Colab'a yükle veya Google Drive'dan bağla
2. Bu scripti bir Colab hücresine yapıştır ve çalıştır
"""

# ============================================================
# 1) Kurulum
# ============================================================
# !pip install ultralytics

# ============================================================
# 2) Import ve Ayarlar
# ============================================================
import os
import shutil
import random
from pathlib import Path
from ultralytics import YOLO

# Tekrarlanabilirlik için seed
SEED = 42
random.seed(SEED)

# --- AYARLAR (ihtiyacına göre değiştir) ---
SOURCE_DIR    = "/content/archive/images"    # Colab'daki klasör (resim + label aynı yerde)
DATASET_DIR   = "/content/dataset"           # Oluşturulacak dataset klasörü
VAL_RATIO     = 0.2                          # %20 validation
MODEL_NAME    = "yolo11s.pt"                 # Model adı (yolo11s, yolov8s, yolo12s vb.)
EPOCHS        = 300                          # Max epoch
PATIENCE      = 30                           # Early stopping: 30 epoch boyunca iyileşme olmazsa dur
BATCH_SIZE    = 16                           # GPU belleğine göre ayarla (T4: 16, A100: 32-64)
IMG_SIZE      = 640                          # Resim boyutu
NUM_CLASSES   = 1                            # Sınıf sayısı
CLASS_NAMES   = ["plate"]                    # Plaka tespiti - tek sınıf

# ============================================================
# 3) Dataset Klasör Yapısını Oluştur (train/val split)
# ============================================================
for split in ["train", "val"]:
    os.makedirs(f"{DATASET_DIR}/{split}/images", exist_ok=True)
    os.makedirs(f"{DATASET_DIR}/{split}/labels", exist_ok=True)

# Resim dosyalarını listele
all_images = sorted([f for f in os.listdir(SOURCE_DIR) if f.endswith((".jpg", ".jpeg", ".png"))])
print(f"Toplam resim sayısı: {len(all_images)}")

# Karıştır ve böl
random.shuffle(all_images)
val_count = int(len(all_images) * VAL_RATIO)
val_images = set(all_images[:val_count])
train_images = set(all_images[val_count:])

print(f"Train: {len(train_images)}, Val: {len(val_images)}")

# Dosyaları kopyala
copied = {"train": 0, "val": 0}
skipped = 0

for img_name in all_images:
    split = "val" if img_name in val_images else "train"
    label_name = Path(img_name).stem + ".txt"

    # Label dosyasını kontrol et (aynı klasörde)
    label_src = os.path.join(SOURCE_DIR, label_name)
    if not os.path.exists(label_src):
        skipped += 1
        continue

    # Kopyala
    shutil.copy2(os.path.join(SOURCE_DIR, img_name), f"{DATASET_DIR}/{split}/images/{img_name}")
    shutil.copy2(label_src, f"{DATASET_DIR}/{split}/labels/{label_name}")
    copied[split] += 1

print(f"Kopyalanan -> Train: {copied['train']}, Val: {copied['val']}, Atlanan: {skipped}")

# ============================================================
# 4) Dataset YAML Dosyası Oluştur
# ============================================================
yaml_content = f"""path: {DATASET_DIR}
train: train/images
val: val/images

nc: {NUM_CLASSES}
names: {CLASS_NAMES}
"""

yaml_path = f"{DATASET_DIR}/dataset.yaml"
with open(yaml_path, "w") as f:
    f.write(yaml_content)

print(f"\nDataset YAML oluşturuldu: {yaml_path}")
print(yaml_content)

# ============================================================
# 5) Modeli Yükle ve Eğit (Early Stopping dahil)
# ============================================================
model = YOLO(MODEL_NAME)

results = model.train(
    data=yaml_path,
    epochs=EPOCHS,
    patience=PATIENCE,        # Early stopping
    batch=BATCH_SIZE,
    imgsz=IMG_SIZE,
    device=0,                 # GPU
    workers=2,
    seed=SEED,
    # Optimizer
    optimizer="auto",
    lr0=0.01,
    lrf=0.01,
    # Augmentation
    hsv_h=0.015,
    hsv_s=0.7,
    hsv_v=0.4,
    degrees=0.0,
    translate=0.1,
    scale=0.5,
    fliplr=0.5,
    mosaic=1.0,
    # Kayıt
    project="/content/runs",
    name="opet_yolo",
    save=True,
    save_period=50,           # Her 50 epoch'ta checkpoint kaydet
    plots=True,
    verbose=True,
)

# ============================================================
# 6) Sonuçları Göster
# ============================================================
print("\n" + "=" * 50)
print("Eğitim tamamlandı!")
print(f"En iyi model: /content/runs/opet_yolo/weights/best.pt")
print(f"Son model:    /content/runs/opet_yolo/weights/last.pt")
print("=" * 50)

# Validation sonuçlarını göster
metrics = model.val()
print(f"\nmAP50:    {metrics.box.map50:.4f}")
print(f"mAP50-95: {metrics.box.map:.4f}")
