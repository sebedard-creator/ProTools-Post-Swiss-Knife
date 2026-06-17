import os
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from utils.text_utils import format_text_for_pdf, transform_track_name_for_excel, extract_clip_name_and_comment, tc_to_seconds, extract_track_code_and_actor

def create_markers_pdf(markers, title, output_path):
    """Create a compact PDF listing of markers"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                          rightMargin=0.75*inch, leftMargin=0.75*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Marker style - compact with hanging indent
    marker_style = ParagraphStyle(
        'MarkerStyle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        leftIndent=0,
        firstLineIndent=0,
        spaceBefore=3,
        spaceAfter=3,
        leading=12,
        fontName='Helvetica'
    )
    
    # Add title
    title_para = Paragraph(f"MARKERS - {title}", title_style)
    elements.append(title_para)
    elements.append(Spacer(1, 0.2*inch))
    
    # Add markers
    for marker in markers:
        timecode = marker['timecode']
        text = marker['text']
        
        # Format: "HH:MM:SS - Marker text"
        marker_line = f"<b>{timecode}</b> - {text}"
        marker_para = Paragraph(marker_line, marker_style)
        elements.append(marker_para)
    
    # Build PDF
    doc.build(elements)

def create_pdf(data, output_path):
    """Create a PDF from the parsed cue sheet data"""
    doc = SimpleDocTemplate(output_path, pagesize=letter,
                          rightMargin=0.5*inch, leftMargin=0.5*inch,
                          topMargin=0.75*inch, bottomMargin=0.5*inch)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Title style
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#333333'),
        spaceAfter=20,
        alignment=TA_CENTER
    )
    
    # Section header style
    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2C5F8D'),
        spaceAfter=12,
        spaceBefore=20,
        bold=True
    )
    
    # Cell text style - supports text wrapping
    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.HexColor('#333333'),
        alignment=TA_LEFT,
        wordWrap='LTR'
    )
    
    # Add title (session name)
    title = Paragraph(data.get('title', data['session_name']), title_style)
    elements.append(title)
    elements.append(Spacer(1, 0.3*inch))
    
    # Process each track
    for track in data['tracks']:
        # Add track name as section header
        track_header = Paragraph(track['name'], section_style)
        elements.append(track_header)
        elements.append(Spacer(1, 0.1*inch))
        
        # Create table data with Paragraph objects for text wrapping
        table_data = []
        
        for event in track['events']:
            # Wrap each cell in a Paragraph for proper text handling
            row = [
                Paragraph(event['start_time'], cell_style),
                Paragraph(event['end_time'], cell_style),
                Paragraph(event['duration'], cell_style),
                Paragraph(event['clip_name'], cell_style),
                Paragraph(event['state'], cell_style) if event['state'] else Paragraph('', cell_style)
            ]
            table_data.append(row)
        
        if table_data:
            # Create table with adjusted column widths
            # Reduced state column since it's often empty or short text
            table = Table(table_data, colWidths=[1.1*inch, 1.1*inch, 0.9*inch, 3.2*inch, 1.3*inch])
            
            # Style the table
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#333333')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            
            elements.append(table)
            elements.append(Spacer(1, 0.3*inch))
    
    # Build PDF
    doc.build(elements)

def make_text_cell(formatted_text, text_style, show_arrow=False):
    """
    Build the content for a TEXTE table cell.
    If show_arrow is True, wraps content in a mini nested table
    with a blue ▼ arrow aligned bottom-right, indicating the next
    cue follows within 2 seconds.
    """
    from reportlab.platypus import Table, TableStyle, Paragraph
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_RIGHT

    if not show_arrow:
        return Paragraph(formatted_text, text_style)

    # Arrow style: small, blue, right-aligned
    arrow_style = ParagraphStyle(
        'ArrowStyle',
        parent=text_style,
        fontSize=9,
        textColor=colors.HexColor('#7AAFD4'),
        alignment=TA_RIGHT,
        spaceBefore=2,
        leading=10
    )

    inner = Table(
        [
            [Paragraph(formatted_text, text_style)],
            [Paragraph('↓', arrow_style)]
        ],
        colWidths=None  # Will inherit from outer cell
    )
    inner.setStyle(TableStyle([
        ('LEFTPADDING',   (0, 0), (-1, -1), 0),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 0),
        ('TOPPADDING',    (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return inner

def create_adr_acteur_pdf(track, track_code, actor_name, filename, output_path):
    """Create ADR recording PDF for actor (ACTEUR version)"""
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from datetime import datetime
    import tempfile
    import os
    
    def build_elements():
        """Generate a fresh set of PDF elements - can be called multiple times"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'TrackTitle',
            parent=styles['Heading1'],
            fontSize=14,
            bold=True,
            spaceAfter=12
        )
        
        # Cell style for text - larger (13pt)
        text_cell_style = ParagraphStyle(
            'TextCellStyle',
            parent=styles['Normal'],
            fontSize=13,
            leading=15
        )
        
        # Cell style for timecodes - smaller
        tc_cell_style = ParagraphStyle(
            'TcCellStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=12,
            alignment=TA_CENTER
        )
        
        # Header style
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=10,
            bold=True,
            alignment=TA_CENTER
        )
        
        # Get display track name
        display_name = transform_track_name_for_excel(track['name'])
        
        # Add title
        title = Paragraph(f"<b>{display_name}</b>", title_style)
        elements.append(title)
        
        # Add convocation line if present
        if track.get('comments'):
            convocation_style = ParagraphStyle(
                'ConvocationStyle',
                parent=styles['Normal'],
                fontSize=11,
                leading=14,
                spaceAfter=8
            )
            convocation = Paragraph(f"<b>Convocation:</b> {track['comments']}", convocation_style)
            elements.append(convocation)
        
        elements.append(Spacer(1, 0.1*inch))
        
        # Prepare table data
        table_data = []
        
        # Headers
        headers = [
            Paragraph("<b>CUE</b>", header_style),
            Paragraph("<b>TC IN</b>", header_style),
            Paragraph("<b>TC OUT</b>", header_style),
            Paragraph("<b>DURÉE</b>", header_style),
            Paragraph("<b>TEXTE</b>", header_style)
        ]
        table_data.append(headers)
        
        # Data rows
        for i, event in enumerate(track['events'], 1):
            clip_name, comment = extract_clip_name_and_comment(event['clip_name'])
            
            # Format text: remove quotes and italicize parentheses
            formatted_text = format_text_for_pdf(clip_name)
            
            # Detect if next cue follows within 2 seconds
            show_arrow = False
            if i <= len(track['events']) - 1:  # not the last cue
                next_event = track['events'][i]  # i is 1-based so this is the next one
                tc_out = tc_to_seconds(event['end_time'])
                tc_in_next = tc_to_seconds(next_event['start_time'])
                if tc_out is not None and tc_in_next is not None:
                    show_arrow = (tc_in_next - tc_out) <= 2
            
            # Format cue number: letters on top, numbers on bottom
            if track_code:
                cue = f"{track_code}<br/>{i:02d}"
            else:
                cue = f"{i:02d}"
            
            row = [
                Paragraph(cue, tc_cell_style),
                Paragraph(event['start_time'], tc_cell_style),
                Paragraph(event['end_time'], tc_cell_style),
                Paragraph(event['duration'][3:], tc_cell_style),  # Remove first 3 characters (00:)
                make_text_cell(formatted_text, text_cell_style, show_arrow)
            ]
            table_data.append(row)
        
        # Create table with further reduced widths - maximize TEXT column
        table = Table(table_data, colWidths=[0.5*inch, 0.9*inch, 0.9*inch, 0.7*inch, 7.0*inch], repeatRows=1)
        
        # Style the table
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
            ('ALIGN', (0, 1), (3, -1), 'CENTER'),  # Center CUE and timecodes
            ('ALIGN', (4, 1), (4, -1), 'LEFT'),     # Left align text
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
    
    # FIRST PASS: Build to temporary file to count total pages
    temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(temp_fd)
    
    try:
        # Create temporary document and build
        temp_doc = SimpleDocTemplate(temp_path, pagesize=landscape(letter),
                          rightMargin=0.5*inch, leftMargin=0.5*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
        temp_doc.build(build_elements())  # Build with first set of elements
        total_pages = temp_doc.page  # Get total page count
        
        # SECOND PASS: Build real PDF with correct page numbers
        def add_footer(canvas, doc):
            """Footer callback with total page count"""
            canvas.saveState()
            page_num = canvas.getPageNumber()
            date_str = datetime.now().strftime("%Y/%m/%d")
            footer_text = f"Page {page_num}/{total_pages}     {filename}     {date_str}"
            canvas.setFont('Helvetica-Bold', 9)
            canvas.drawCentredString(landscape(letter)[0]/2, 0.5*inch, footer_text)
            canvas.restoreState()
        
        # Build the real PDF with fresh elements
        real_doc = SimpleDocTemplate(output_path, pagesize=landscape(letter),
                          rightMargin=0.5*inch, leftMargin=0.5*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
        real_doc.build(build_elements(), onFirstPage=add_footer, onLaterPages=add_footer)
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)

def create_adr_technicien_pdf(track, track_code, actor_name, filename, output_path):
    """Create ADR recording PDF for technician (TECHNICIEN version)"""
    from reportlab.lib.pagesizes import landscape, letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from datetime import datetime
    import tempfile
    import os
    
    def build_elements():
        """Generate a fresh set of PDF elements - can be called multiple times"""
        elements = []
        styles = getSampleStyleSheet()
        
        # Title style
        title_style = ParagraphStyle(
            'TrackTitle',
            parent=styles['Heading1'],
            fontSize=12,
            bold=True,
            spaceAfter=12
        )
        
        # Cell style for text
        text_cell_style = ParagraphStyle(
            'TextCellStyle',
            parent=styles['Normal'],
            fontSize=10,
            leading=12
        )
        
        # Cell style for timecodes - smaller, centered
        tc_cell_style = ParagraphStyle(
            'TcCellStyle',
            parent=styles['Normal'],
            fontSize=9,
            leading=11,
            alignment=TA_CENTER
        )
        
        # Header style
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=9,
            bold=True,
            alignment=TA_CENTER
        )
        
        # Smaller header style for TAKE SELECT/ALT columns
        header_small_style = ParagraphStyle(
            'HeaderSmallStyle',
            parent=styles['Normal'],
            fontSize=7,
            bold=True,
            alignment=TA_CENTER
        )
        
        # Get display track name
        display_name = transform_track_name_for_excel(track['name'])
        
        # Add title
        title = Paragraph(f"<b>{display_name}</b>", title_style)
        elements.append(title)
        
        # Add convocation line if present
        if track.get('comments'):
            convocation_style = ParagraphStyle(
                'ConvocationStyle',
                parent=styles['Normal'],
                fontSize=10,
                leading=12,
                spaceAfter=6
            )
            convocation = Paragraph(f"<b>Convocation:</b> {track['comments']}", convocation_style)
            elements.append(convocation)
        
        elements.append(Spacer(1, 0.1*inch))
        
        # Prepare table data
        table_data = []
        
        # Headers
        headers = [
            Paragraph("<b>CUE</b>", header_style),
            Paragraph("<b>TC IN</b>", header_style),
            Paragraph("<b>TC OUT</b>", header_style),
            Paragraph("<b>DURÉE</b>", header_style),
            Paragraph("<b>TEXTE</b>", header_style),
            Paragraph("<b>COMMENTAIRE</b>", header_style),
            Paragraph("<b>TAKE<br/>SELECT</b>", header_small_style),
            Paragraph("<b>TAKE<br/>ALT</b>", header_small_style)
        ]
        table_data.append(headers)
        
        # Data rows
        for i, event in enumerate(track['events'], 1):
            clip_name, comment = extract_clip_name_and_comment(event['clip_name'])
            
            # Format text: remove quotes and italicize parentheses
            formatted_text = format_text_for_pdf(clip_name)
            formatted_comment = format_text_for_pdf(comment) if comment else ""
            
            # Detect if next cue follows within 2 seconds
            show_arrow = False
            if i <= len(track['events']) - 1:  # not the last cue
                next_event = track['events'][i]  # i is 1-based so this is the next one
                tc_out = tc_to_seconds(event['end_time'])
                tc_in_next = tc_to_seconds(next_event['start_time'])
                if tc_out is not None and tc_in_next is not None:
                    show_arrow = (tc_in_next - tc_out) <= 2
            
            # Format cue number with line break between code and number
            if track_code:
                cue = f"{track_code}<br/>{i:02d}"
            else:
                cue = f"{i:02d}"
            
            row = [
                Paragraph(cue, tc_cell_style),
                Paragraph(event['start_time'], tc_cell_style),
                Paragraph(event['end_time'], tc_cell_style),
                Paragraph(event['duration'][3:], tc_cell_style),  # Remove first 3 characters (00:)
                make_text_cell(formatted_text, text_cell_style, show_arrow),
                Paragraph(formatted_comment, text_cell_style),
                Paragraph("", tc_cell_style),  # Empty space instead of checkbox
                Paragraph("", tc_cell_style)   # Empty space instead of checkbox
            ]
            table_data.append(row)
        
        # Create table with further reduced widths - maximize TEXT and COMMENTAIRE columns
        table = Table(table_data, 
                     colWidths=[0.45*inch, 0.85*inch, 0.85*inch, 0.65*inch, 3.7*inch, 2.3*inch, 0.6*inch, 0.6*inch],
                     repeatRows=1)
        
        # Style the table
        table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E8F0F8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, 0), 6),
            
            # Data rows
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('ALIGN', (0, 1), (3, -1), 'CENTER'),  # Center CUE and timecodes
            ('ALIGN', (4, 1), (5, -1), 'LEFT'),     # Left align text and comments
            ('ALIGN', (6, 1), (7, -1), 'CENTER'),   # Center empty take columns
            ('VALIGN', (0, 1), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F5F5F5')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 1), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ]))
        
        elements.append(table)
        return elements
    
    # FIRST PASS: Build to temporary file to count total pages
    temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf')
    os.close(temp_fd)
    
    try:
        # Create temporary document and build
        temp_doc = SimpleDocTemplate(temp_path, pagesize=landscape(letter),
                          rightMargin=0.5*inch, leftMargin=0.5*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
        temp_doc.build(build_elements())  # Build with first set of elements
        total_pages = temp_doc.page  # Get total page count
        
        # SECOND PASS: Build real PDF with correct page numbers
        def add_footer(canvas, doc):
            """Footer callback with total page count"""
            canvas.saveState()
            page_num = canvas.getPageNumber()
            date_str = datetime.now().strftime("%Y/%m/%d")
            footer_text = f"Page {page_num}/{total_pages}     {filename}     {date_str}"
            canvas.setFont('Helvetica-Bold', 8)
            canvas.drawCentredString(landscape(letter)[0]/2, 0.5*inch, footer_text)
            canvas.restoreState()
        
        # Build the real PDF with fresh elements
        real_doc = SimpleDocTemplate(output_path, pagesize=landscape(letter),
                          rightMargin=0.5*inch, leftMargin=0.5*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
        real_doc.build(build_elements(), onFirstPage=add_footer, onLaterPages=add_footer)
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_path):
            os.remove(temp_path)
