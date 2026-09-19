import time
import cv2
import numpy as np
from typing import Tuple, Optional, Callable, Dict, Any

class StabilityDetector:
    """
    Mendeteksi perubahan frame dan memastikan teks visual novel yang sedang
    mengalami animasi ketikan (typewriter effect) telah sepenuhnya stabil
    sebelum diekstraksi oleh OCR.
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = config or {}
        stab_cfg = cfg.get("stability", {})
        self.change_threshold = cfg.get("change_threshold", 40000)
        self.stable_threshold = stab_cfg.get("stable_threshold", 1.5)
        self.consecutive_stable_frames = stab_cfg.get("consecutive_stable_frames", 3)
        self.check_interval = stab_cfg.get("check_interval", 0.15)
        self.max_wait_seconds = stab_cfg.get("max_wait_seconds", 3.5)

    def detect_change(self, current_img: np.ndarray, prev_small_gray: Optional[np.ndarray]) -> Tuple[bool, np.ndarray]:
        """
        Memeriksa apakah terjadi perubahan visual signifikan pada area dialog.
        """
        gray = cv2.cvtColor(current_img, cv2.COLOR_BGR2GRAY)
        small = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)

        if prev_small_gray is None:
            return True, small

        diff = cv2.absdiff(small, prev_small_gray)
        sum_diff = np.sum(diff)

        if sum_diff > self.change_threshold:
            return True, small
        return False, prev_small_gray

    def wait_until_stable(self, grab_fn: Callable[[], np.ndarray]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Menunggu hingga animasi ketikan (typewriter effect) berhenti sepenuhnya.
        Membutuhkan N frame berturut-turut yang stabil untuk memastikan render tidak terputus di tengah kalimat.
        Mengembalikan gambar akhir dan representasi frame kecilnya untuk memperbarui state.
        """
        start_time = time.time()
        prev_small = None
        consecutive_stable = 0

        latest_img = grab_fn()

        while True:
            img = grab_fn()
            latest_img = img

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            small = cv2.resize(gray, (0, 0), fx=0.25, fy=0.25)

            if prev_small is not None:
                diff = cv2.absdiff(small, prev_small)
                mean_diff = np.mean(diff)

                if mean_diff < self.stable_threshold:
                    consecutive_stable += 1
                    if consecutive_stable >= self.consecutive_stable_frames:
                        # Frame telah stabil secara konsisten
                        current_small_half = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)
                        return latest_img, current_small_half
                else:
                    # Masih ada karakter baru yang sedang muncul
                    consecutive_stable = 0

            prev_small = small

            # Batas toleransi keamanan maksimal
            if time.time() - start_time > self.max_wait_seconds:
                current_small_half = cv2.resize(gray, (0, 0), fx=0.5, fy=0.5)
                return latest_img, current_small_half

            time.sleep(self.check_interval)
