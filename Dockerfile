FROM python:3.10-slim

# Instalacja systemowych zależności dla libGL, Pillow, pdf2slides
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Ustaw katalog roboczy
WORKDIR /app

# Skopiuj requirements.txt i zainstaluj zależności Pythona
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Skopiuj resztę plików aplikacji
COPY . .

# Streamlit port
EXPOSE 8501

# Uruchom Streamlit
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
