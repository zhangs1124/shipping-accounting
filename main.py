from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse

import models
from database import engine
from routers import ships, voyages, charge_items, invoices, invoice_lines, customers

# 建立所有資料表
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="船務部帳務系統")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# 掛載路由
app.include_router(ships.router)
app.include_router(voyages.router)
app.include_router(charge_items.router)
app.include_router(invoices.router)
app.include_router(invoice_lines.router)
app.include_router(customers.router)


@app.get("/")
def root():
    return RedirectResponse(url="/invoices")
