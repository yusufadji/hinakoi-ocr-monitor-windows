# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2026-09-19

### Added
- **Direct Sub-Region Capture** (`src/capture.py`): Direct bounding box screen capture via `mss` to minimize CPU and RAM overhead.
- **Dynamic Stability Detector** (`src/stability.py`): Multi-frame consecutive check to eliminate premature typewriter cut-offs and render flicker.
- **Image Preprocessing** (`src/preprocessor.py`): Lanczos-4 high-fidelity upscaling with channel-safe OpenCV handling.
- **Modular OCR Engines** (`src/ocr_engine.py`): Abstraction for EasyOCR and MangaOCR, with tuned thresholds (`low_text=0.25`, `text_threshold=0.55`) for ellipsis detection.
- **Dual-Layer Post-Processing** (`src/postprocessor.py`): CJK whitespace removal, quote auto-balancing, and Levenshtein-based deduplication.
- **Domain Lexicon** (`lexicon.json`): Regex-based error correction for visual novel kanji (`僕`, `傘の先輩`, `後輩`, `天真爛漫`, `小首を傾げる`, `経緯`, etc.) and character roster.
- **Centralized Configuration** (`config.json`): Settings for monitor selection, ROI coordinates, thresholds, and player name replacement.
- **Benchmark Evaluation** (`tests/evaluate_accuracy.py`): Multi-chapter evaluation script demonstrating error reduction up to 55.48%.

### Changed
- Refactored `main.py` to use the modular architecture with UTF-8 stdout reconfiguration.
- Updated `README.md` with v2.1 architecture overview, pipeline flow diagram, configuration guide, and benchmark results.
- Updated `requirements.txt` with `manga-ocr`, `transformers`, and `rapidfuzz`.
- Updated `.gitignore` to ignore local data folders (`raw`, `revised`, `transcript`, `__pycache__`).

### Fixed
- Fixed OpenCV `(-15:Bad number of channels)` error in EasyOCR by validating image channels before conversion.
- Fixed case-sensitive player name replacement where `THEKONz` and `THE先輩` were skipped.
- Fixed inverted quotes where character names were trapped inside opening brackets.
