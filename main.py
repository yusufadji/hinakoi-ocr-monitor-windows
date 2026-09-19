import os
import sys
import json
import time
import datetime
from typing import Dict, Any

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from src.capture import ScreenCapturer
from src.stability import StabilityDetector
from src.preprocessor import ImagePreprocessor
from src.ocr_engine import create_ocr_engine, MangaOCREngine
from src.postprocessor import TextPostprocessor

CONFIG_PATH = "config.json"
LEXICON_PATH = "lexicon.json"

def load_config() -> Dict[str, Any]:
    default_config = {
        "monitor_index": 2,
        "crop_regions": {
            "subtitle": {
                "top_ratio": 0.68,
                "bottom_ratio": 0.93,
                "left_ratio": 0.06,
                "right_ratio": 0.94
            }
        },
        "ocr_engine": "manga-ocr",
        "fallback_engine": "easyocr",
        "upscale_factor": 1.6,
        "change_threshold": 40000,
        "stability": {
            "stable_threshold": 1.5,
            "consecutive_stable_frames": 3,
            "check_interval": 0.15,
            "max_wait_seconds": 3.5
        },
        "loop_delay": 0.25,
        "destination": "transcript",
        "player_name_replacement": {
            "enabled": True,
            "source_name": "THEKONZ",
            "target_placeholder": "PLAYER_NAME"
        }
    }

    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                default_config.update(loaded)
        except Exception as e:
            print(f"[WARN] Gagal membaca {CONFIG_PATH}: {e}. Menggunakan pengaturan default.")

    return default_config

def main():
    print("=" * 60)
    print("  Hinakoi Story Transcriber (OCR Monitor) - Optimized v2.0")
    print("=" * 60)

    config = load_config()
    destination = config.get("destination", "transcript")
    os.makedirs(destination, exist_ok=True)
    transcript_file = os.path.join(destination, "transcript.txt")

    # Inisialisasi modul
    monitor_index = config.get("monitor_index", 2)
    capturer = ScreenCapturer(monitor_index=monitor_index)
    subtitle_roi = capturer.calculate_roi_box(config["crop_regions"]["subtitle"])
    print(f"[INFO] Monitor: {monitor_index} | ROI Box: {subtitle_roi}")

    stability_detector = StabilityDetector(config=config)
    preprocessor = ImagePreprocessor(upscale_factor=config.get("upscale_factor", 1.6))
    ocr_engine = create_ocr_engine(
        engine_name=config.get("ocr_engine", "manga-ocr"),
        fallback_name=config.get("fallback_engine", "easyocr")
    )
    postprocessor = TextPostprocessor(config=config, lexicon_path=LEXICON_PATH)

    prev_small_gray = None
    loop_delay = config.get("loop_delay", 0.25)

    print(f"\n[INFO] Memulai monitoring visual novel secara real-time...")
    print(f"[INFO] Hasil transkripsi akan disimpan ke: {transcript_file}")
    print("[INFO] Tekan Ctrl+C untuk menghentikan program.\n" + "-" * 60)

    try:
        while True:
            # 1. Direct sub-region capture (ringan & cepat)
            current_roi = capturer.grab_roi(subtitle_roi)

            # 2. Deteksi perubahan frame
            changed, current_small = stability_detector.detect_change(current_roi, prev_small_gray)
            if not changed:
                time.sleep(0.15)
                continue

            # 3. Tunggu hingga animasi ketikan (typewriter effect) benar-benar stabil
            stable_img, prev_small_gray = stability_detector.wait_until_stable(
                lambda: capturer.grab_roi(subtitle_roi)
            )

            # 4. Preprocessing citra sesuai tipe engine
            if isinstance(ocr_engine, MangaOCREngine):
                processed = preprocessor.preprocess_for_manga_ocr(stable_img)
            else:
                processed = preprocessor.preprocess_for_easyocr(stable_img)

            # 5. Inferensi OCR
            raw_text = ocr_engine.recognize(processed)

            # 6. Post-processing (CJK space removal, balancing quotes, kamus lexicon, deduplikasi)
            should_save, is_replacement, clean_text = postprocessor.evaluate_difference(raw_text)

            if should_save:
                timestamp = datetime.datetime.now().strftime("%H:%M:%S")

                if is_replacement:
                    print(f"[{timestamp}] [UPDATE]: {clean_text}")
                    # Perbarui baris terakhir pada file transcript jika ada
                    if os.path.exists(transcript_file):
                        with open(transcript_file, "r", encoding="utf-8") as f:
                            lines = f.readlines()
                        if lines:
                            lines[-1] = clean_text + "\n"
                            with open(transcript_file, "w", encoding="utf-8") as f:
                                f.writelines(lines)
                        else:
                            with open(transcript_file, "a", encoding="utf-8") as f:
                                f.write(clean_text + "\n")
                else:
                    print(f"\n[{timestamp}] NEW TEXT:")
                    print(clean_text)
                    print("-" * 60)
                    with open(transcript_file, "a", encoding="utf-8") as f:
                        f.write(clean_text + "\n")

            time.sleep(loop_delay)

    except KeyboardInterrupt:
        print("\n\n[INFO] Program dihentikan oleh pengguna.")
    except Exception as e:
        print(f"\n[ERROR] Terjadi kesalahan: {e}")
    finally:
        capturer.close()
        print("[INFO] ScreenCapturer ditutup dengan aman.")

if __name__ == "__main__":
    main()