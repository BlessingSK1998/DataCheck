FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN useradd -m -u 1000 appuser
COPY --chown=appuser:appuser . .
USER appuser
ENV PORT=7860
EXPOSE 7860
CMD ["sh", "-c", "python -m streamlit run app.py --server.address=0.0.0.0 --server.port=${PORT:-7860} --server.headless=true"]
