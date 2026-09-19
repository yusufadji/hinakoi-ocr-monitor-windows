import cv2
import numpy as np
import mss
from typing import Dict, Any, Tuple

class ScreenCapturer:
    """
    Menangani penangkapan layar efisien menggunakan mss secara native di Windows.
    Mendukung direct sub-region capture untuk meminimalkan beban CPU dan memori.
    """
    def __init__(self, monitor_index: int = 2):
        self.sct = mss.mss()
        self.monitor_index = monitor_index
        self.validate_monitor_index()

    def validate_monitor_index(self):
        total_monitors = len(self.sct.monitors) - 1
        if self.monitor_index >= len(self.sct.monitors):
            print(f"[WARN] Monitor index {self.monitor_index} tidak ditemukan. Menggunakan monitor utama (1).")
            self.monitor_index = 1

    def get_monitor(self) -> Dict[str, int]:
        return self.sct.monitors[self.monitor_index]

    def calculate_roi_box(self, roi_ratios: Dict[str, float]) -> Dict[str, int]:
        """
        Menghitung bounding box absolut mss berdasarkan rasio relatif terhadap monitor tertarget.
        """
        mon = self.get_monitor()
        left = int(mon["left"] + mon["width"] * roi_ratios.get("left_ratio", 0.0))
        top = int(mon["top"] + mon["height"] * roi_ratios.get("top_ratio", 0.0))
        width = int(mon["width"] * (roi_ratios.get("right_ratio", 1.0) - roi_ratios.get("left_ratio", 0.0)))
        height = int(mon["height"] * (roi_ratios.get("bottom_ratio", 1.0) - roi_ratios.get("top_ratio", 0.0)))

        return {"left": left, "top": top, "width": width, "height": height}

    def grab_roi(self, roi_box: Dict[str, int]) -> np.ndarray:
        """
        Mengambil cuplikan area layar spesifik secara langsung dan mengonversinya ke format BGR OpenCV.
        """
        sct_img = self.sct.grab(roi_box)
        img_array = np.array(sct_img)
        return cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)

    def grab_full(self) -> np.ndarray:
        """
        Mengambil seluruh layar monitor tertarget.
        """
        mon = self.get_monitor()
        sct_img = self.sct.grab(mon)
        img_array = np.array(sct_img)
        return cv2.cvtColor(img_array, cv2.COLOR_BGRA2BGR)

    def close(self):
        self.sct.close()
