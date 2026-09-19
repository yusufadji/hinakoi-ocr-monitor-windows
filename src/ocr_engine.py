import abc
import numpy as np
from PIL import Image
import cv2
import torch
from typing import Optional, Dict, Any

class BaseOCREngine(abc.ABC):
    """
    Antarmuka abstrak untuk engine OCR.
    """
    @abc.abstractmethod
    def recognize(self, img_bgr: np.ndarray) -> str:
        pass

class MangaOCREngine(BaseOCREngine):
    """
    Engine OCR berbasis Vision Transformer khusus teks media Jepang (manga, LN, VN).
    Menghasilkan akurasi mendekati sempurna untuk kanji kompleks tanpa spasi acak.
    """
    def __init__(self, force_cpu: bool = False):
        try:
            from manga_ocr import MangaOcr
        except ImportError:
            raise ImportError("Paket 'manga-ocr' belum terinstal. Silakan instal via: pip install manga-ocr")

        print("[INFO] Menginisialisasi model Manga-OCR (Vision Transformer)...")
        # MangaOcr secara otomatis mendeteksi CUDA jika tersedia
        self.model = MangaOcr(force_cpu=force_cpu)
        print("[INFO] Manga-OCR berhasil dimuat.")

    def recognize(self, img_bgr: np.ndarray) -> str:
        # Konversi BGR ke RGB PIL Image
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)
        text = self.model(pil_img)
        return text.strip()

class EasyOCREngine(BaseOCREngine):
    """
    Engine fallback menggunakan EasyOCR dengan penyesuaian parameter untuk VN.
    """
    def __init__(self, use_gpu: Optional[bool] = None):
        import easyocr
        if use_gpu is None:
            use_gpu = torch.cuda.is_available()
        print(f"[INFO] Menginisialisasi EasyOCR (GPU: {use_gpu})...")
        self.reader = easyocr.Reader(['ja', 'en'], gpu=use_gpu)
        print("[INFO] EasyOCR berhasil dimuat.")

    def recognize(self, img: np.ndarray) -> str:
        if len(img.shape) == 3 and img.shape[2] >= 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
        # Penyetelan threshold agar titik elipsis (……) dan tanda baca kecil tidak dianggap derau
        results = self.reader.readtext(
            gray,
            detail=0,
            paragraph=True,
            low_text=0.25,
            text_threshold=0.55,
            contrast_ths=0.1,
            adjust_contrast=0.5
        )
        return "".join(results).strip()

def create_ocr_engine(engine_name: str = "manga-ocr", fallback_name: str = "easyocr") -> BaseOCREngine:
    """
    Factory function untuk menginisialisasi OCR engine dengan fallback otomatis yang aman.
    """
    if engine_name.lower() in ["manga-ocr", "manga_ocr", "manga"]:
        try:
            return MangaOCREngine()
        except Exception as e:
            print(f"[WARN] Gagal memuat Manga-OCR ({e}). Beralih ke fallback engine: {fallback_name}...")
            return EasyOCREngine()

    elif engine_name.lower() in ["easyocr", "easy"]:
        return EasyOCREngine()

    else:
        print(f"[WARN] Engine '{engine_name}' tidak dikenal. Menggunakan EasyOCR.")
        return EasyOCREngine()
