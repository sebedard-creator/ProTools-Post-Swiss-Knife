# 🎬 ProTools Post Swiss Knife

> L'interface est offerte en français; le code et la documentation technique contiennent aussi des termes anglais propres aux formats Pro Tools.

A comprehensive web application designed to convert Avid Pro Tools session exports (.txt, .csv, .xls, .xlsx) into multiple formats ready for post-production workflows (PDF, Excel, PTX, AAF, EDL).

## 📁 Features (What the Swiss Knife does)

The application provides a simple drag-and-drop web interface allowing you to convert files with a single click.

### 📍 Markers & Spotting (Input: `.txt`)
- **MARKERS**: Exports Pro Tools session markers into a compact PDF (Timecode + Name).
- **SPOTTING**: Creates a PDF listing all clips per track with IN/OUT timecodes, duration, clip name, and muted/unmuted state.

### 🎙️ ADR (Input: `.txt`)
- **ADR CHARACTER ORDER**: Creates an Excel file organized by character. Each section displays the name followed by the number of lines, then the cues with timecodes, duration, text, and comments.
- **ADR TC ORDER**: Creates an Excel file containing all cues from all characters in a single list sorted by timecode.
- **ADR RECORDING**: Generates a ZIP file containing two PDFs per character (ACTOR sheet and TECHNICIAN sheet with alternative takes).

### 🔄 Conversions & Session Formats
- **CSV TO EDL**: Converts a CSV file (from a notes template) into a Pro Tools EDL (.edl).
- **CSV TO PDF (TC ORDER)**: Converts a notes CSV into a PDF sorted by timecode.
- **CSV TO AAF (FAKE AUDIO TRACKS)**: Direct conversion from a CSV to an AAF containing empty audio clips, with a mode suffix (Production or Sound Design).
- **XLS TO PTX MARKERS**: Generates a native Pro Tools session (`.ptx`) containing a Memory Locations (markers) track at 23.976 fps directly from an Excel file. Powered by the custom `pt_api` for native decryption, it automatically maps columns and bypasses Pro Tools' character limits.
- **CSV TO PTX**: Rebuilds a native Playback Notes Sync session from its UTF-8 CSV export. Each note becomes a 2-second empty Clip Group at the correct timecode, using the same tracks and PTX template as the mobile app. The accepted time formats are compact `MMSS` (for example `4112`) and legacy session timecode `HH:MM:SS:` (for example `10:41:12:`); impossible timecodes are rejected with their CSV line number.

#### CSV TO PTX — Playback Notes Sync format

The CSV must be UTF-8 and contain the standard headers `TIME CODE`, `MIX`, `DIAL`, `FX`, `STP`, `FOL`, `ADR`, `CON`, `DONE`, and `NOTES`. One category must be marked `X` on every exported row. `FX`, `STP`, `FOL`, and `CON` map respectively to the template tracks `SFX`, `STEPS`, `FOLEY`, and `CONCEP`; clip-group names come from `NOTES`.

## 🚀 Usage (Local vs Cloud)

### Option 1: Local Usage
The code can run standalone on your computer.
1. Run `START_WINDOWS.bat` on Windows or `START_MAC.sh` on macOS.
2. Open your web browser at `http://localhost:5000`.

### Option 2: Web Deployment (Render.com)
The application is 100% cloud-ready (managed entirely in RAM via `io.BytesIO` and `tempfile` to prevent user collisions) and can be hosted for free.
1. Push the code to a public **GitHub** repository.
2. Link the repository to **Render.com** by creating a new **Web Service**.
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `gunicorn app:app`
5. The application will automatically update (CI/CD) every time a "Push" is made to the main GitHub branch.

## 🔧 Architecture & Dependencies

- **Web Framework**: Flask / Gunicorn
- **PDF Manipulation**: ReportLab
- **Excel Manipulation**: OpenPyXL
- **AAF Manipulation**: pyaaf2
- **PTX Manipulation**: Custom native API (`pt_api` 1.5.1) loaded from Git through `requirements.txt`.
- The project includes a `.gitignore` and `requirements.txt` ready for production.

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---
*Conçu par Sébastien Bédard*
