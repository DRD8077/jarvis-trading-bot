from fastapi import FastAPI
from fastapi.responses import FileResponse
import uvicorn, os

app = FastAPI()

@app.get("/download-apk")
async def download_apk():
    path = "/workspaces/codespaces-blank/JARVIS-Nuclear-AI-v3.0.apk"
    return FileResponse(
        path,
        media_type="application/vnd.android.package-archive",
        filename="JARVIS-Nuclear-AI-v3.0.apk"
    )

@app.get("/apk")
async def apk_page():
    return {"name": "JARVIS-Nuclear-AI-v3.0.apk", "size": "32MB", "download": "/download-apk"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9090)
