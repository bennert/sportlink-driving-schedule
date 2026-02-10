"""
Script om markdown rijschema te converteren naar PDF
"""
import os
import re

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

def cleanup_pdfs(directory):
    """ Remove PDF files """
    if not os.path.exists(directory):
        return

    for file in os.listdir(directory):
        if file.endswith('.pdf'):
            full_path = os.path.join(directory, file)
            try:
                os.remove(full_path)
                print(f"  Removed PDF: {file}")
            except OSError as e:
                print(f"  Could not remove {file}: {e}")

# Input en output paths
script_dir = os.path.dirname(os.path.abspath(__file__))
markdown_folder = os.path.join(script_dir, "docs")

# Check for flag files that indicate which markdown files to convert
flag_files = [file for file in os.listdir(markdown_folder) if file.endswith(".flag")]

if not flag_files:
    print("No changes detected - no PDF conversion needed")
    exit(0)
else:
    # Clean up PDF files
    cleanup_pdfs(markdown_folder)

# Collect all markdown files that need to be converted
markdown_files_to_convert = []
for flag_file in flag_files:
    flag_path = os.path.join(markdown_folder, flag_file)
    with open(flag_path, 'r', encoding='utf-8') as f:
        files = [
            line.strip() for line in f.readlines()[:-1]
            if os.path.exists(os.path.join(script_dir, line.strip()))
        ]
        markdown_files_to_convert.extend(files)

print(f"\nConverting {len(markdown_files_to_convert)} markdown file(s) to PDF...")

for markdown_file in markdown_files_to_convert:
    if not os.path.exists(markdown_file):
        print(f"File not found: {markdown_file}")
        continue

    # Lees de markdown file
    with open(markdown_file, 'r', encoding='utf-8') as f:
        markdown_text = f.read()
    output_pdf = markdown_file.replace('.md', '.pdf')
    # Create PDF document met landscape orientatie voor betere tabel weergave
    pdf = SimpleDocTemplate(output_pdf, pagesize=landscape(A4))
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#333333'),
        spaceAfter=30,
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#555555'),
        spaceAfter=20,
        spaceBefore=20,
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
    )

    # Parse markdown content
    story = []
    lines = markdown_text.split('\n')
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Heading 1
        if line.startswith('# '):
            text = line[2:].strip()
            story.append(Paragraph(text, title_style))
            story.append(Spacer(1, 12))

        # Heading 2
        elif line.startswith('## '):
            text = line[3:].strip()
            story.append(Paragraph(text, heading_style))
            story.append(Spacer(1, 12))

        # Table (detect markdown table)
        elif line.startswith('|'):
            table_data = []
            # Collect all table rows
            while i < len(lines) and lines[i].strip().startswith('|'):
                row = [cell.strip() for cell in lines[i].strip().split('|')[1:-1]]
                # Skip separator row (the one with --- )
                if not all('---' in cell or cell == '' for cell in row):
                    # Parse markdown links and convert to Paragraph objects with clickable links
                    parsed_row = []
                    for cell in row:
                        # Check if cell contains a markdown link [text](url)
                        link_match = re.match(r'\[([^\]]+)\]\(([^\)]+)\)', cell)
                        if link_match:
                            text = link_match.group(1)
                            url = link_match.group(2)
                            # Create a Paragraph with a clickable link
                            cell_style = ParagraphStyle(
                                'CellLink',
                                parent=normal_style,
                                fontSize=7,
                                textColor=colors.HexColor('#0066cc'),
                            )
                            parsed_row.append(
                                Paragraph(
                                    f'<link href="{url}" color="blue">{text}</link>', cell_style))
                        else:
                            parsed_row.append(cell)
                    table_data.append(parsed_row)
                i += 1
            i -= 1  # Adjust because we'll increment at the end of the loop

            if table_data:
                col_widths = [
                    0.7*inch,   # Datum
                    0.6*inch,   # Dag
                    1.8*inch,   # Samenvatting
                    1.0*inch,   # Tijd @Strijp
                    0.5*inch,   # Start
                    0.5*inch,   # Einde
                    2.2*inch,   # Locatie
                    0.7*inch,   # Reis kosten
                    0.6*inch,   # Reis km
                    0.7*inch,   # Reis minuten
                ]

                # Create table with styling en kolombreedtes
                t = Table(table_data, colWidths=col_widths)
                t.setStyle(TableStyle([
                    # Header row styling
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('TOPPADDING', (0, 0), (-1, 0), 8),

                    # Data rows styling
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 7),
                    ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1),
                     [colors.white, colors.HexColor('#f2f2f2')]),
                    ('TOPPADDING', (0, 1), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('WORDWRAP', (0, 0), (-1, -1), True),
                ]))
                story.append(t)
                story.append(Spacer(1, 20))

        # Normal text
        elif line:
            story.append(Paragraph(line, normal_style))
            story.append(Spacer(1, 6))

        i += 1

    # Build PDF
    pdf.build(story)

    print(f"PDF succesvol aangemaakt: {output_pdf}")
