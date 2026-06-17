#!/usr/bin/env python3
"""
CSV to PDF Converter (TC Order) for Pro Tools Swiss Knife
Converts a CSV cue sheet into a PDF sorted by timecode with 3 columns:
TC IN | NOTE (track name) | COMMENTAIRE
"""

import sys
import csv
import re
from pathlib import Path
from datetime import datetime
import tempfile
import os

from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def normalize_tc(tc_str):
    """
    Normalize timecode to HH:MM:SS (no frames, no trailing colon).
    Input might be '10:36:30:' or '10:36:30:00' or '10:36:30'.
    """
    tc_str = tc_str.strip()
    parts = [p for p in tc_str.split(':') if p != '']
    # Keep only the first 3 parts (HH, MM, SS), drop frames if present
    if len(parts) >= 3:
        return f"{parts[0]}:{parts[1]}:{parts[2]}"
    return tc_str


def tc_to_sort_key(tc_str):
    """Convert HH:MM:SS to a sortable integer (total seconds)."""
    parts = tc_str.split(':')
    try:
        h = int(parts[0])
        m = int(parts[1])
        s = int(parts[2])
        return h * 3600 + m * 60 + s
    except (ValueError, IndexError):
        return 0


def parse_csv(csv_file):
    """
    Parse the CSV and return a list of entries (one per track-hit) sorted by TC.
    Each entry is a dict: {'tc': str, 'note': str (track name), 'comment': str}
    """
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        rows = list(reader)

    if len(rows) < 2:
        raise ValueError("CSV file must have at least 2 rows (header + data)")

    headers = rows[0]

    # TC column = 0 (always)
    tc_col = 0

    # Find NOTES column
    notes_col = None
    for i, header in enumerate(headers):
        if header.strip().upper() in ['NOTES', 'NOTE']:
            notes_col = i
            break
    if notes_col is None:
        raise ValueError("Could not find NOTES column in CSV")

    # Track columns: between TC and NOTES, excluding DONE/STATUS/COMPLETE/empty
    track_columns = []
    for i in range(1, notes_col):
        header = headers[i].strip()
        if header and header.upper() not in ['DONE', 'STATUS', 'COMPLETE']:
            track_columns.append({'index': i, 'name': header})

    # Build entries
    entries = []
    for row_num, row in enumerate(rows[1:], start=2):
        if len(row) < 2 or not row[tc_col].strip():
            continue  # skip empty rows

        tc = normalize_tc(row[tc_col])
        comment = row[notes_col].strip() if notes_col < len(row) else ""

        # For each track column marked with X/x, create an entry
        for track in track_columns:
            col_idx = track['index']
            if col_idx < len(row):
                cell = row[col_idx].strip().lower()
                if cell == 'x':
                    entries.append({
                        'tc': tc,
                        'note': track['name'],
                        'comment': comment,
                        'sort_key': tc_to_sort_key(tc),
                    })

    # Sort by TC
    entries.sort(key=lambda e: e['sort_key'])
    return entries


def create_pdf(entries, filename, output_path):
    """
    Create the PDF with 3 columns: TC IN | NOTE | COMMENTAIRE
    Same visual style as ADR Recording PDFs (landscape letter, blue header,
    alternating rows, footer with page count + filename + date).
    """

    def build_elements():
        """Generate a fresh set of PDF elements - can be called multiple times."""
        elements = []
        styles = getSampleStyleSheet()

        # Title style
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontSize=14,
            bold=True,
            spaceAfter=12,
        )

        # Cell style for comment text - larger
        text_cell_style = ParagraphStyle(
            'TextCellStyle',
            parent=styles['Normal'],
            fontSize=13,
            leading=15,
        )

        # Cell style for TC and NOTE - smaller, centered
        tc_cell_style = ParagraphStyle(
            'TcCellStyle',
            parent=styles['Normal'],
            fontSize=11,
            leading=13,
            alignment=TA_CENTER,
        )

        # Header style
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=10,
            bold=True,
            alignment=TA_CENTER,
        )

        # Title = filename (without extension)
        title_text = filename.rsplit('.', 1)[0] if '.' in filename else filename
        title = Paragraph(f"<b>{title_text}</b>", title_style)
        elements.append(title)
        elements.append(Spacer(1, 0.1 * inch))

        # Table data
        table_data = []

        # Headers
        headers = [
            Paragraph("<b>TC IN</b>", header_style),
            Paragraph("<b>NOTE</b>", header_style),
            Paragraph("<b>COMMENTAIRE</b>", header_style),
        ]
        table_data.append(headers)

        # Data rows
        for entry in entries:
            row = [
                Paragraph(entry['tc'], tc_cell_style),
                Paragraph(entry['note'], tc_cell_style),
                Paragraph(entry['comment'] or '', text_cell_style),
            ]
            table_data.append(row)

        # Column widths - 10" usable (landscape letter, 0.5" margins each side)
        # TC IN narrow, NOTE narrow, COMMENTAIRE gets the rest
        table = Table(
            table_data,
            colWidths=[1.2 * inch, 1.0 * inch, 7.8 * inch],
            repeatRows=1,
        )

        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8F0F8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),

            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 1), (1, -1), 'CENTER'),   # Center TC and NOTE
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),     # Left align COMMENTAIRE
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))

        elements.append(table)
        return elements

    # FIRST PASS: build to temp to count total pages
    temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(temp_fd)

    try:
        temp_doc = SimpleDocTemplate(
            temp_path, pagesize=landscape(letter),
            rightMargin=0.5 * inch, leftMargin=0.5 * inch,
            topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        )
        temp_doc.build(build_elements())
        total_pages = temp_doc.page

        # SECOND PASS: real PDF with correct page numbers in footer
        def add_footer(canvas, doc):
            canvas.saveState()
            page_num = canvas.getPageNumber()
            date_str = datetime.now().strftime("%Y/%m/%d")
            footer_text = f"Page {page_num}/{total_pages}     {filename}     {date_str}"
            canvas.setFont('Helvetica-Bold', 9)
            canvas.drawCentredString(landscape(letter)[0] / 2, 0.5 * inch, footer_text)
            canvas.restoreState()

        real_doc = SimpleDocTemplate(
            output_path, pagesize=landscape(letter),
            rightMargin=0.5 * inch, leftMargin=0.5 * inch,
            topMargin=0.75 * inch, bottomMargin=0.75 * inch,
        )
        real_doc.build(build_elements(), onFirstPage=add_footer, onLaterPages=add_footer)

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def csv_to_pdf_tcorder(csv_file, output_pdf):
    """
    Main entry point. Convert CSV cue sheet to a TC-ordered PDF.
    """
    print(f"\n{'='*60}")
    print(f"CSV to PDF Converter (TC Order)")
    print(f"{'='*60}")
    print(f"Input:  {csv_file}")
    print(f"Output: {output_pdf}")
    print(f"{'='*60}\n")

    entries = parse_csv(csv_file)
    print(f"Parsed {len(entries)} entries (sorted by TC)")
    for e in entries[:10]:
        print(f"  {e['tc']}  |  {e['note']}  |  {e['comment'][:60]}")
    if len(entries) > 10:
        print(f"  ... and {len(entries) - 10} more")

    if not entries:
        raise ValueError("No entries found in CSV (no rows with X markers)")

    filename = Path(csv_file).name
    create_pdf(entries, filename, output_pdf)

    print(f"\n✓ PDF created: {output_pdf}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("\nUsage: python CSV_to_PDF_TCOrder.py <input_csv_file>")
        sys.exit(1)

    csv_path = Path(sys.argv[1])
    if not csv_path.exists():
        print(f"ERROR: File not found: {csv_path}")
        sys.exit(1)

    output_pdf = csv_path.with_suffix('.pdf')
    csv_to_pdf_tcorder(str(csv_path), str(output_pdf))
