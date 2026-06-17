# 🎬 Cue Sheet Converter

A simple web application that converts Avid Pro Tools cue sheet text files into formatted PDFs or Excel spreadsheets.

## 📁 What's Included

- `app.py` - The main application
- `requirements.txt` - Required Python libraries
- `templates/index.html` - Web interface
- `INSTALLATION_GUIDE.md` - Complete step-by-step installation instructions
- `START_WINDOWS.bat` - Quick start script for Windows
- `START_MAC.sh` - Quick start script for Mac
- `example_output_FIXED.pdf` - Example PDF output (SPOTTING format)
- `example_ADR_VALIDATION.xlsx` - Example Excel output (ADR VALIDATION format)

## 🚀 Quick Start

### First Time Setup:
1. Read `INSTALLATION_GUIDE.md` for complete installation instructions
2. Install Python (if not already installed)
3. Install dependencies: `pip install -r requirements.txt`

### Daily Use:

**Windows:** 
- **With window:** Double-click `START_WINDOWS.bat`
- **Hidden (no window):** Double-click `START_HIDDEN.vbs`
- **Auto-open browser:** Double-click `START_AND_OPEN.bat`

**Mac:** 
- Double-click `START_MAC.sh` (or run `./START_MAC.sh` in Terminal)

**To Stop (Windows):**
- Double-click `STOP_APPLICATION.bat` (or use Task Manager)

Then open your browser to `http://localhost:5000`

## 💡 How It Works

1. Start the application using the startup script
2. Open the web interface in your browser
3. Upload your Avid cue sheet (.txt file)
4. Choose your output format:
   - **SPOTTING**: PDF with full details (Start, End, Duration, Clip Name, Mute Status)
   - **ADR VALIDATION**: Excel spreadsheet (Start, End, Duration, Clip Name, Comment)
   - **ADR RECORDING**: Multiple PDFs in ZIP (Actor + Technician sheets for each track)
5. Click "Convert" and download your file!

## 📱 Access from Other Devices

The application runs on your PC and can be accessed from any device on your local network:
- From the same computer: `http://localhost:5000`
- From other devices: `http://YOUR-IP-ADDRESS:5000` (IP shown when app starts)

## 🔧 Requirements

- Python 3.8 or higher
- Windows PC or Mac
- Web browser

## 📖 Need Help?

Check the `INSTALLATION_GUIDE.md` file for detailed instructions and troubleshooting.

## ✨ Features

- Simple drag-and-drop interface
- **Two output formats:**
  - **SPOTTING**: Professional PDF with all details including mute status
  - **ADR VALIDATION**: Clean Excel spreadsheet with 4 columns
- Converts multiple tracks (SPOTTING FOLEY, SPOTTING FOOTSTEPS, etc.)
- Handles special characters (É, Ó, etc.)
- Shortened timecodes (removes frame numbers)
- Works on local network (access from Mac or PC)
- No internet connection required

---

Made with ❤️ for your daily workflow
