FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Create unprivileged container user
RUN groupadd -r streamlit && useradd -r -g streamlit streamlit

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend source
COPY . .

RUN chown -R streamlit:streamlit /app

USER streamlit

EXPOSE 8501

# Force bind Streamlit correctly to enable OIDC and Websocket bridges
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--browser.serverAddress=0.0.0.0", "--server.enableCORS=false"]
