import cv2
import numpy as np
from typing import Tuple, Optional

class ImagePreprocessor:
    """
    Melakukan preprocessing citra visual novel untuk meningkatkan ketajaman
    karakter kanji kompleks dan mengeliminasi noise dari background semi-transparan.
    """
    def __init__(self, upscale_factor: float = 1.6):
        self.upscale_factor = upscale_factor

    def enhance_contrast(self, gray: np.ndarray) -> np.ndarray:
        """
        Menerapkan CLAHE (Contrast Limited Adaptive Histogram Equalization)
        untuk memperjelas perbedaan antara inti font putih dan outline hitam.
        """
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray)

    def unsharp_mask(self, image: np.ndarray, sigma: float = 1.0, strength: float = 1.5) -> np.ndarray:
        """
        Menajamkan tepi guratan kanji (unsharp masking) agar goresan padat tidak menyatu.
        """
        blurred = cv2.GaussianBlur(image, (0, 0), sigma)
        sharpened = cv2.addWeighted(image, 1.0 + strength, blurred, -strength, 0)
        return sharpened

    def preprocess_for_manga_ocr(self, img_bgr: np.ndarray) -> np.ndarray:
        """
        Optimasi citra untuk model Vision Transformer (manga-ocr).
        Mempertahankan ketajaman tekstur dengan interpolasi Lanczos berkualitas tinggi.
        """
        h, w = img_bgr.shape[:2]
        new_w = int(w * self.upscale_factor)
        new_h = int(h * self.upscale_factor)

        # Upscale dengan Lanczos4 untuk menjaga integritas garis tepi
        upscaled = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

        # Konversi ke RGB karena manga-ocr / PIL menggunakan urutan RGB
        img_rgb = cv2.cvtColor(upscaled, cv2.COLOR_BGR2RGB)
        return img_rgb

    def preprocess_for_easyocr(self, img: np.ndarray, enhance: bool = False) -> np.ndarray:
        """
        Optimasi citra untuk EasyOCR (grayscale dan Lanczos4 upscale berkualitas tinggi).
        """
        if len(img.shape) == 3 and img.shape[2] >= 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img

        # Upscale berkualitas tinggi
        h, w = gray.shape[:2]
        new_w = int(w * self.upscale_factor)
        new_h = int(h * self.upscale_factor)
        upscaled = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_LANCZOS4)

        if enhance:
            enhanced = self.enhance_contrast(upscaled)
            return self.unsharp_mask(enhanced, sigma=0.8, strength=1.2)

        return upscaled
