import re
import json
import os
from typing import Dict, Any, List, Optional, Tuple

class TextPostprocessor:
    """
    Menyempurnakan hasil teks OCR:
    - Menghapus spasi tidak wajar pada teks bahasa Jepang (CJK).
    - Menormalkan tanda baca (tanda seru, tanda tanya, elipsis, kurung/kutip).
    - Menerapkan kamus domain khusus (lexicon.json) untuk memperbaiki salah baca Kanji.
    - Menangani deduplikasi cerdas (substring & fuzzy matching).
    """
    def __init__(self, config: Optional[Dict[str, Any]] = None, lexicon_path: str = "lexicon.json"):
        self.config = config or {}
        self.lexicon = self.load_lexicon(lexicon_path)
        self.last_text = ""
        self.cjk_pattern = re.compile(r'[\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF00-\uFFEF]')

    def load_lexicon(self, path: str) -> Dict[str, Any]:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[WARN] Gagal membaca lexicon dari {path}: {e}")
        return {"regex_replacements": [], "characters": []}

    def remove_cjk_spaces(self, text: str) -> str:
        """
        Menghapus spasi yang diapit oleh karakter CJK (Kanji, Kana, atau tanda baca Jepang),
        namun tetap mempertahankan spasi antar kata Latin / alfabet.
        """
        # Hapus spasi antara karakter CJK dan karakter CJK lainnya
        pattern1 = re.compile(r'([\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF00-\uFFEF])\s+([\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF00-\uFFEF])')
        prev = ""
        result = text
        while prev != result:
            prev = result
            result = pattern1.sub(r'\1\2', result)

        # Hapus spasi di akhir kalimat terputus (misal: "かもしれな し" -> "かもしれなし")
        result = re.sub(r'([\u3040-\u309F\u4E00-\u9FFF])\s+([\u3040-\u309F])', r'\1\2', result)
        return result.strip()

    def normalize_punctuation(self, text: str) -> str:
        """
        Menormalkan tanda baca ASCII ke standar tanda baca Jepang (full-width)
        dan memastikan tanda kutip serta tanda kurung berpasangan.
        """
        # Konversi tanda baca umum
        text = text.replace("!", "！")
        text = text.replace("?", "？")
        text = text.replace("~", "～")

        # Normalisasi elipsis variatif ke bentuk standar
        text = re.sub(r'\.{3,}', '……', text)
        text = re.sub(r'…+', '……', text)
        text = re.sub(r'‥+', '……', text)

        # Auto-balancing tanda kutip dialog 「 ... 」
        if "「" in text and "」" not in text:
            text = text + "」"
        elif "」" in text and "「" not in text:
            # Jika ada nama karakter di awal, sisipkan setelah nama
            for char_name in self.lexicon.get("characters", []):
                if text.startswith(char_name):
                    rest = text[len(char_name):].strip()
                    text = f"{char_name} 「{rest}"
                    break
            else:
                if not text.startswith("「"):
                    text = "「" + text

        # Auto-balancing kurung monolog batin （ ... ） atau ( ... )
        if text.startswith("(") and text.endswith(")"):
            text = "（" + text[1:-1] + "）"
        elif text.endswith(")") and not text.startswith("("):
            text = "（" + text[:-1] + "）"
        elif text.endswith("）") and "（" not in text:
            text = "（" + text

        return text

    def apply_lexicon(self, text: str) -> str:
        """
        Menerapkan kamus penggantian domain Hinakoi dan perbaikan kanji umum.
        """
        for rule in self.lexicon.get("regex_replacements", []):
            pattern = rule.get("pattern")
            replacement = rule.get("replacement")
            if pattern and replacement:
                text = re.sub(pattern, replacement, text)

        # Ganti nama akun pemain jika dikonfigurasi (case-insensitive & toleran variasi OCR)
        player_cfg = self.config.get("player_name_replacement", {})
        if player_cfg.get("enabled", False):
            source = player_cfg.get("source_name", "THEKONZ")
            target = player_cfg.get("target_placeholder", "PLAYER_NAME")
            if source:
                base_name = re.escape(source.rstrip("Zz0"))
                pattern = rf"(?i)\b{base_name}[Zz0]?\b|{base_name}[Zz0]?"
                text = re.sub(pattern, target, text)
                # Tangani juga kasus dimana EasyOCR hanya menangkap 'THE' sebelum '先輩'
                text = re.sub(r"(?i)\bTHE\b(?=先輩)", target, text)

        # Perbaiki jika nama karakter tertelan ke dalam tanda kutip pembuka (misal: 「鶴崎仁香 THE先輩... -> 鶴崎仁香「THE先輩...)
        for char_name in self.lexicon.get("characters", []):
            quote_inside_pattern = rf'^[「（]({re.escape(char_name)})\s*'
            if re.search(quote_inside_pattern, text):
                text = re.sub(quote_inside_pattern, rf'{char_name}「', text)
                break

        return text

    def process(self, raw_text: str) -> str:
        """
        Menjalankan seluruh pipeline post-processing secara berurutan.
        """
        if not raw_text or not raw_text.strip():
            return ""

        text = raw_text.strip()
        text = self.remove_cjk_spaces(text)
        text = self.apply_lexicon(text)
        text = self.normalize_punctuation(text)
        return text

    def evaluate_difference(self, new_text: str) -> Tuple[bool, bool, str]:
        """
        Mengevaluasi apakah teks baru harus disimpan atau diabaikan.
        Mengembalikan (should_save, is_replacement_of_last, final_text).
        """
        clean_text = self.process(new_text)
        if not clean_text:
            return False, False, ""

        if clean_text == self.last_text:
            return False, False, clean_text

        # Jika teks baru adalah kelanjutan lebih lengkap dari teks sebelumnya (misal typewriter yang tersisa)
        if self.last_text and clean_text.startswith(self.last_text) and len(clean_text) > len(self.last_text):
            self.last_text = clean_text
            return True, True, clean_text

        # Cek kesamaan fuzzy untuk menghindari flicker render (hanya jika ada rapidfuzz)
        try:
            from rapidfuzz import fuzz
            ratio = fuzz.ratio(clean_text, self.last_text)
            if ratio > 88 and abs(len(clean_text) - len(self.last_text)) <= 3:
                # Render flicker kecil, pertahankan versi yang lebih panjang atau yang memiliki tanda baca lengkap
                if len(clean_text) > len(self.last_text):
                    self.last_text = clean_text
                    return True, True, clean_text
                return False, False, self.last_text
        except ImportError:
            pass

        self.last_text = clean_text
        return True, False, clean_text
