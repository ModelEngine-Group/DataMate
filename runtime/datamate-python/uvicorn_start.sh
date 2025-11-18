export LOG_LEVEL=DEBUG
export DEBUG=true

uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 18000 \
    --reload