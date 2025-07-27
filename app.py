import streamlit as st
from pdf2slides import Converter
from io import BytesIO

st.title("PDF to PPTX using pdf2slides")

uploaded_file = st.file_uploader("Upload PDF presentation", type="pdf")

if uploaded_file:
    with st.spinner("Converting PDF to PPTX..."):
        converter = Converter()
        output_stream = BytesIO()

        # Convert the uploaded PDF to PPTX (save to file-like object)
        converter.convert(uploaded_file, output_stream)

        # Ensure the stream is at position 0
        output_stream.seek(0)

    st.success("Conversion completed!")

    st.download_button(
        label="Download PPTX",
        data=output_stream,
        file_name="converted.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )