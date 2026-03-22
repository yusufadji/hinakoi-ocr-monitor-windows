# Hinakoi Story Transcriber (OCR)

Alat otomasi berbasis Python untuk mengekstrak dan mentranskrip teks cerita dari game visual novel **Hinakoi** secara _real-time_.

Script ini menggunakan Optical Character Recognition (EasyOCR) untuk membaca layar game yang di-mirror ke PC (via `scrcpy` atau Emulator Android), lalu secara otomatis mendeteksi dialog baru dan menyimpannya ke dalam file `.txt`.

---

## 🌟 Fitur Utama

- **Real-time Transcription:** Membaca dan mencatat dialog karakter secara langsung saat game berjalan.
- **Smart Frame Detection:** Hanya melakukan proses OCR jika mendeteksi adanya perubahan teks atau frame yang sudah stabil, sehingga menghemat _resource_ PC.
- **Multi-Monitor Support:** Mudah disesuaikan untuk menangkap layar dari monitor spesifik (misalnya Monitor 2), berkat library `mss`.
- **GPU Acceleration:** Mendukung PyTorch (CUDA) untuk proses pembacaan teks bahasa Jepang (Kanji/Kana) yang jauh lebih cepat.
- **Auto-Save:** Hasil transkripsi langsung ditambahkan ke dalam file `transcript/transcript.txt` lengkap dengan _timestamp_.

---

## 📋 Prasyarat

Sebelum menjalankan script ini, pastikan sistem kamu memiliki:

1. **OS Windows** 2. **Python 3.8** atau lebih baru.
2. **Perangkat Android & scrcpy** (untuk _screen mirroring_ dari HP fisik) ATAU **Emulator Android** (seperti LDPlayer, BlueStacks, dll).
3. _(Opsional namun sangat disarankan)_ **NVIDIA GPU** dengan CUDA terinstal untuk performa OCR yang optimal.

---

## 🛠️ Instalasi

1. **Clone repositori ini:**

   ```bash
   git clone https://github.com/yusufadji/hinakoi-ocr-monitor-windows.git
   cd hinakoi-ocr-monitor-windows
   ```

2. **Install _dependencies_ dasar:**

   ```bash
   pip install -r requirements.txt
   ```

3. **Install PyTorch (Untuk Dukungan GPU/CUDA):**
   Secara _default_, perintah di atas tidak menginstal PyTorch versi GPU. Agar script berjalan lebih cepat, install PyTorch dengan perintah berikut (contoh untuk CUDA 11.8):
   ```bash
   pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu118](https://download.pytorch.org/whl/cu118)
   ```
   _(Cek [situs resmi PyTorch](https://pytorch.org/get-started/locally/) untuk versi CUDA lainnya)._

---

## 🚀 Cara Penggunaan

### 1. Persiapan Layar Game

Jalankan game Hinakoi melalui perangkatmu.

- **Jika menggunakan HP fisik:** Hubungkan HP ke PC dan jalankan `scrcpy`. Pindahkan _window_ scrcpy ke monitor yang ingin kamu rekam (misal: Monitor 2).
- **Jika menggunakan Emulator:** Buka emulator dan pindahkan _window_-nya ke monitor target. Posisikan dalam mode _Fullscreen_ atau ukuran jendela yang maksimal.

### 2. Konfigurasi Script

Buka file `main.py` menggunakan teks editor pilihanmu dan sesuaikan konfigurasi berikut jika diperlukan:

```python
# Ganti dengan indeks monitor tempat game berjalan.
# 1 = Monitor Utama, 2 = Monitor Kedua, dst.
MONITOR_INDEX = 2
```

_Catatan: Area crop subtitle sudah disetel untuk rasio Full HD (1080p). Jika teks terpotong, sesuaikan nilai pada fungsi `crop_subtitle()` atau pastikan Scaling UI Windows kamu berada di 100%._

### 3. Jalankan Transkripsi

Buka terminal/CMD di dalam folder proyek, lalu jalankan:

```bash
python main.py
```

Script akan mulai memonitor layar. Setiap kali ada teks dialog baru yang stabil di layar, script akan mencetaknya ke terminal dan menyimpannya secara otomatis ke `transcript/transcript.txt`.

Tekan `Ctrl + C` di terminal untuk menghentikan program.

---

## ⚠️ Batasan & Catatan

- **UI Scaling Windows:** Pastikan _Display Scaling_ pada pengaturan Windows untuk monitor target disetel ke **100%**. Jika diatur lebih dari itu (misal 125%), area penangkapan layar (`mss`) bisa meleset.
- **Font Jepang:** EasyOCR sudah disetel untuk membaca teks bahasa Jepang (`['ja', 'en']`). Akurasi sangat bergantung pada tingkat kejelasan _render_ dari emulator/scrcpy.

---

## 📜 Disclaimer

Proyek ini adalah alat _fan-made_ dan tidak berafiliasi, dikelola, atau didukung oleh _developer_ maupun _publisher_ dari game Hinakoi. Gunakan script ini secara bertanggung jawab dan murni untuk keperluan pribadi.
