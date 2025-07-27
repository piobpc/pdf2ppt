FROM python:3.10-slim

# Instalacja zależności systemowych (libGL1!)
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && apt-get clean

# Ustawienie katalogu roboczego
WORKDIR /app

# Kopiowanie plików
COPY requirements.txt packages.txt ./
COPY . .

# Instalacja Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Port dla Streamlit
EXPOSE 8501

# Komenda uruchamiająca Streamlit
CMD ["streamlit", "run", "streamlit_app.py"]