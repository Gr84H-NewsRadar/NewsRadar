from fastapi import FastAPI

app = FastAPI(
    title="NewsRadar API",
    description="API REST para gestión de usuarios, alertas, notificaciones, fuentes y canales RSS.",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
    openapi_url="/api/v1/openapi.json"
)

@app.get("/api/v1/health", tags=["system"])
def health_check():
    return {"status": "ok", "version": "1.0.0"}