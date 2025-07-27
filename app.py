import streamlit as st
import pdfplumber
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from io import BytesIO
import os

st.title("PDF to PPTX Converter - Advanced Layout")

uploaded_file = st.file_uploader("Upload PDF presentation", type="pdf")

def add_textbox(slide, text, left, top, width, height, font_size=14, bold=False):
    textbox = slide.shapes.add_textbox(left, top, width, height)
    tf = textbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.alignment = PP_ALIGN.LEFT
    p.font.color.rgb = RGBColor(0, 0, 0)
    return textbox

def add_image(slide, image_bytes, left, top, max_width, max_height):
    from PIL import Image
    img = Image.open(BytesIO(image_bytes))
    width, height = img.size
    ratio = min(max_width / width, max_height / height)
    new_width = int(width * ratio)
    new_height = int(height * ratio)

    image_stream = BytesIO()
    img.save(image_stream, format='PNG')
    image_stream.seek(0)

    slide.shapes.add_picture(image_stream, left, top, width=Inches(new_width/96), height=Inches(new_height/96))

if uploaded_file:
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    with pdfplumber.open(uploaded_file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            slide_layout = prs.slide_layouts[6]  # blank slide
            slide = prs.slides.add_slide(slide_layout)

            # Get slide dimensions in points (pptx uses English Metric Units - EMU)
            slide_width = prs.slide_width  # in EMU
            slide_height = prs.slide_height

            # Extract words with positions
            words = page.extract_words(extra_attrs=["fontname", "size", "x0", "top", "x1", "bottom"])

            # Group words by their vertical position (roughly line by line)
            lines = []
            current_line = []
            current_top = None
            tolerance = 3  # pts tolerance for line breaks

            for w in words:
                if current_top is None:
                    current_top = w['top']
                    current_line = [w]
                elif abs(w['top'] - current_top) < tolerance:
                    current_line.append(w)
                else:
                    lines.append(current_line)
                    current_line = [w]
                    current_top = w['top']
            if current_line:
                lines.append(current_line)

            # For each line, join words and get bounding box
            for line in lines:
                text = " ".join(word['text'] for word in line)
                x0 = min(word['x0'] for word in line)
                top = min(word['top'] for word in line)
                x1 = max(word['x1'] for word in line)
                bottom = max(word['bottom'] for word in line)

                # Scale coordinates to slide size
                # pdfplumber coordinates: origin top-left, units: pts (1/72 inch)
                # slide_width, slide_height in EMU (914400 EMU = 1 inch)
                # Conversion: pts to inches (pts/72), then inches to EMU (inch*914400)
                left = Inches(x0 / 72)
                top_pos = Inches(top / 72)
                width = Inches((x1 - x0) / 72)
                height = Inches((bottom - top) / 72)

                # Add textbox per line (font size relative to pdf font size)
                # Pdf font size might not be reliable, so use default or from 'size' attribute
                font_size = line[0].get('size', 12)
                bold = False
                add_textbox(slide, text, left, top_pos, width, height, font_size=font_size, bold=bold)

            # Extract images
            images = page.images
            for img_obj in images:
                try:
                    # Crop image from page bbox, get image bytes
                    # pdfplumber images coordinates: x0,y0,x1,y1 in pts
                    x0, top, x1, bottom = img_obj['x0'], img_obj['top'], img_obj['x1'], img_obj['bottom']
                    crop = page.within_bbox((x0, top, x1, bottom)).to_image(resolution=150)
                    img_bytes = crop.original

                    left = Inches(x0 / 72)
                    top_pos = Inches(top / 72)
                    max_width = Inches((x1 - x0) / 72)
                    max_height = Inches((bottom - top) / 72)

                    add_image(slide, img_bytes, left, top_pos, max_width*96, max_height*96)
                except Exception as e:
                    st.warning(f"Nie udało się wstawić obrazka: {e}")

    output_stream = BytesIO()
    prs.save(output_stream)
    output_stream.seek(0)

    st.download_button(
        label="Download PPTX",
        data=output_stream,
        file_name="converted.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )