import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse

app = FastAPI(title="HTTPS Redirector")

@app.middleware("http")
async def https_redirect(request: Request, call_next):
    # 擷取目前的 host 並將 port 換成 8443 (HTTPS)
    host = request.url.hostname
    port = 8443
    url = f"https://{host}:{port}{request.url.path}"
    if request.url.query:
        url += f"?{request.url.query}"
    return RedirectResponse(url=url, status_code=301)

if __name__ == "__main__":
    # 此伺服器專門接收原本的 8000 Port 流量
    uvicorn.run(app, host="0.0.0.0", port=8000)
