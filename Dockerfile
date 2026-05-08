FROM python:3.10-slim

WORKDIR /app

# Kerakli tizim paketlari
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# pip yangilash
RUN pip install --no-cache-dir --upgrade pip

# Avval PyTorch (CPU versiyasi) alohida indeksdan o'rnatiladi
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Keyin qolgan paketlar default PyPI'dan o'rnatiladi
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "app.py"]
