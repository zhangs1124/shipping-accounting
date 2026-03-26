from fastapi.templating import Jinja2Templates
from fastapi import Request

def inject_user(request: Request):
    # 從 request.state 取得由 middleware 注入的 user
    return {"current_user": getattr(request.state, "user", None)}

# 改用建構式傳入 context_processors，這在大多數版本都支援
templates = Jinja2Templates(directory="templates", context_processors=[inject_user])
