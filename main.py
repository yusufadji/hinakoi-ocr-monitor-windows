import cv2
import numpy as np
import easyocr
import time
import datetime
import torch
import mss
import os

# ==========================
# CONFIG
# ==========================

# Ganti HDMI_OUTPUT dengan urutan monitor di Windows
# 1 = Monitor Utama, 2 = Monitor Kedua, dst. (0 = Semua monitor digabung)
MONITOR_INDEX = 2

CHANGE_THRESHOLD = 50000        # sensitivitas deteksi perubahan
STABLE_THRESHOLD = 2            # frame dianggap stabil
CHECK_INTERVAL = 0.25           # delay saat menunggu stabil
LOOP_DELAY = 0.3                # delay loop utama
UPSCALE_FACTOR = 1.6            # upscale ringan untuk kanji kompleks

USE_GPU = torch.cuda.is_available()

print("GPU Available:", USE_GPU)

reader = easyocr.Reader(['ja', 'en'], gpu=USE_GPU)

last_text = ""
prev_gray = None
destination = "transcript"

# Pastikan folder tujuan ada
os.makedirs(destination, exist_ok=True)

# Inisialisasi mss untuk screen capture
sct = mss.mss()

# ==========================
# CAPTURE (WINDOWS VERSION)
# ==========================

def capture_monitor():
    # Ambil resolusi dan posisi monitor yang dipilih
    monitor = sct.monitors[MONITOR_INDEX]
    sct_img = sct.grab(monitor)
    
    # Konversi raw pixels ke numpy array
    img_array = np.array(sct_img)
    
    # mss menangkap layar dalam format BGRA, konversi ke BGR agar kompatibel dengan cv2
    img = cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)
    return img

# ==========================
# CROP SUBTITLE AREA (FHD tuned)
# ==========================

def crop_subtitle(img):
    h, w, _ = img.shape
    return img[
        int(h * 0.68):int(h * 0.93),
        int(w * 0.06):int(w * 0.94)
    ]

# ==========================
# PREPROCESS (VN SAFE MODE)
# ==========================

def preprocess(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Upscale ringan (membantu kanji kompleks)
    gray = cv2.resize(
        gray,
        None,
        fx=UPSCALE_FACTOR,
        fy=UPSCALE_FACTOR,
        interpolation=cv2.INTER_LINEAR
    )

    return gray

# ==========================
# FRAME CHANGE DETECTION
# ==========================

def frame_changed(current_img, prev_gray):
    gray = cv2.cvtColor(current_img, cv2.COLOR_BGR2GRAY)

    # kecilkan hanya untuk deteksi
    small = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)

    if prev_gray is None:
        return True, small

    diff = cv2.absdiff(small, prev_gray)
    sum_diff = np.sum(diff)

    if sum_diff > CHANGE_THRESHOLD:
        return True, small
    else:
        return False, prev_gray

# ==========================
# WAIT UNTIL STABLE
# ==========================

def wait_until_stable():
    start_time = time.time()
    prev = None

    while True:
        img = capture_monitor()
        subtitle = crop_subtitle(img)

        gray = cv2.cvtColor(subtitle, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (0, 0), fx=0.25, fy=0.25)

        if prev is not None:
            diff = cv2.absdiff(small, prev)
            mean_diff = np.mean(diff)

            if mean_diff < STABLE_THRESHOLD:
                return subtitle

        prev = small

        if time.time() - start_time > 1.0:
            return subtitle

        time.sleep(CHECK_INTERVAL)

# ==========================
# MAIN LOOP
# ==========================

print("Starting VN OCR monitor for Windows...\n")

while True:
    try:
        img = capture_monitor()
        subtitle = crop_subtitle(img)

        changed, prev_gray = frame_changed(subtitle, prev_gray)

        if not changed:
            time.sleep(0.2)
            continue

        # tunggu render stabil
        subtitle = wait_until_stable()

        processed = preprocess(subtitle)

        # debug preprocessed image
        # cv2.imwrite("debug_processed.png", processed)

        # detail=0 lebih stabil untuk VN
        results = reader.readtext(
            processed,
            detail=0,
            paragraph=True
        )

        combined_text = " ".join(results).strip()

        if combined_text != "" and combined_text != last_text:
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")

            print(f"\n[{timestamp}] NEW TEXT:")
            print(combined_text)
            print("-" * 60)

            with open(f"{destination}/transcript.txt", "a", encoding="utf-8") as f:
                f.write(combined_text + "\n")

            last_text = combined_text

        time.sleep(LOOP_DELAY)

    except KeyboardInterrupt:
        print("\nStopped by user.")
        break

    except Exception as e:
        print("Error:", e)
        time.sleep(1)