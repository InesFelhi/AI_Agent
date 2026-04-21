FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

COPY requirements.txt ./

# Convert requirements file to UTF-8 if needed, then install dependencies.
RUN python - <<'PY'
from pathlib import Path
p = Path('requirements.txt')
text = p.read_bytes()
try:
    content = text.decode('utf-8')
except UnicodeDecodeError:
    content = text.decode('utf-16')
p.write_text(content, encoding='utf-8')
PY
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "-m", "src.main", "--app", "rag"]
