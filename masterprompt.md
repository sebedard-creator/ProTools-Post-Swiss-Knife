# Master Prompt - PT SK 4.1

## Context
PT SK 4.1 (ProTools Post Swiss Knife 4.1) is a web application designed to convert Avid Pro Tools cue sheet files (.txt and .csv) into formats suitable for ADR (Automated Dialogue Replacement), Spotting, and general post-production tasks.

## Architecture
- **Web Framework**: Flask
- **PDF Generation**: ReportLab
- **Excel Generation**: OpenPyXL
- **AAF Generation**: pyaaf2
- **Environment**: Fully self-contained inside `Y:\PT SK 2.0\venv` for local dev. Deployed on Render.com using `gunicorn`.
- **File Processing**: Uses `tempfile.TemporaryDirectory` and `io.BytesIO` to handle concurrent users in the cloud securely without local file persistence.

### Modules
- `app.py`: Flask initialization and routing.
- `parsers/`: 
  - `avid_parser.py`: Parses ProTools `.txt` files.
  - `excel_parser.py`: Parses `.xls` and `.xlsx` files (used for marker injection).
- `generators/`: 
  - `pdf_generator.py`: Generates Spotting and ADR PDFs.
  - `excel_generator.py`: Generates ADR Excel grids.
  - `aaf_generator.py`: Generates AAF files (Memory Locations/Markers via pyaaf2).
- `utils/`: Common text and formatting utilities.

## Constraints
1. **Self-contained**: No external global dependencies. Everything must run through the local `venv`.
2. **Never overwrite C:\CueSheetConverter**: The old source directory is kept as an archive. All active work happens in `Y:\PT SK 2.0`.
3. **Changelog**: Must be kept up to date in `changelog.md`.
