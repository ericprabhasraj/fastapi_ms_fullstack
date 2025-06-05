from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from routes import user , create_shipment
from core import admin
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await admin.create_default_admin()

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(user.router)
app.include_router(create_shipment.router)

@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/login")
