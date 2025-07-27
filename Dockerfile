FROM python:3.10-bullseye

# Instalacja systemowych bibliotek dla pdf2slides, Pillow, OpenGL
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    poppler-utils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Ustaw katalog roboczy
WORKDIR /app

# Skopiuj pliki requirements.txt i zainstaluj Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Skopiuj resztę plików aplikacji
COPY . .

# Streamlit port
EXPOSE 8501

# Uruchom Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
