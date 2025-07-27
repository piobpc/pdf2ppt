import streamlit as st
import pdfplumber
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN
from io import BytesIO

st.title("PDF to PPTX with Shapes and Layout")

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

def add_shape_rect(slide, left, top, width, height):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(220, 220, 220)
    shape.line.color.rgb = RGBColor(0, 0, 0)
    shape.line.width = Pt(1)

def add_shape_line(slide, x1, y1, x2, y2):
    # PowerPoint API nie ma funkcji do rysowania dowolnej linii między punktami, ale można dodać linię jako kształt "linie"
    # dlatego dodamy prostą linię poziomą lub pionową, a dla innych kątów jest ograniczenie
    # Alternatywa: MSO_SHAPE.LINE_ARROW, ale pozycjonowanie jest bounding box, więc uproszczenie
    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)

    # Jeśli linia jest głównie pozioma:
    if height < width:
        shape = slide.shapes.add_shape(MSO_SHAPE.LINE_ARROW, left, top + height / 2, width, Pt(2))
    else:
        shape = slide.shapes.add_shape(MSO_SHAPE.LINE_ARROW, left + width / 2, top, Pt(2), height)
    shape.line.color.rgb = RGBColor(0, 0, 0)

if uploaded_file:
    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    with pdfplumber.open(uploaded_file) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            slide_layout = prs.slide_layouts[6]  # blank slide
            slide = prs.slides.add_slide(slide_layout)

            # PDF page dimensions in pts
            pdf_width = page.width
            pdf_height = page.height

            # --- Teksty ---
            words = page.extract_words(extra_attrs=["fontname", "size", "x0", "top", "x1", "bottom"])
            lines = []
            current_line = []
            current_top = None
            tolerance = 3

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

            for line in lines:
                text = " ".join(word['text'] for word in line)
                x0 = min(word['x0'] for word in line)
                top = min(word['top'] for word in line)
                x1 = max(word['x1'] for word in line)
                bottom = max(word['bottom'] for word in line)

                left = Inches(x0 / 72)
                top_pos = Inches(top / 72)
                width = Inches((x1 - x0) / 72)
                height = Inches((bottom - top) / 72)

                font_size = line[0].get('size', 12)
                if font_size < 8:
                    font_size = 8  # minimum font size to avoid "ciasno"

                add_textbox(slide, text, left, top_pos, width, height*1.3, font_size=font_size, bold=False)

            # --- Obrazy ---
            for img_obj in page.images:
                try:
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

            # --- Prostokąty ---
            for rect in page.rects:
                x0, top, x1, bottom = rect['x0'], rect['top'], rect['x1'], rect['bottom']
                left = Inches(x0 / 72)
                top_pos = Inches(top / 72)
                width = Inches((x1 - x0) / 72)
                height = Inches((bottom - top) / 72)
                add_shape_rect(slide, left, top_pos, width, height)

            # --- Linie ---
            for line in page.lines:
                x0, top, x1, bottom = line['x0'], line['top'], line['x1'], line['bottom']
                left = Inches(x0 / 72)
                top_pos = Inches(top / 72)
                right = Inches(x1 / 72)
                bottom_pos = Inches(bottom / 72)
                add_shape_line(slide, left, top_pos, right, bottom_pos)

    output_stream = BytesIO()
    prs.save(output_stream)
    output_stream.seek(0)

    st.download_button(
        label="Download PPTX",
        data=output_stream,
        file_name="converted.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )






