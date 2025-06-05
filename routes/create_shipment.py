import os
from datetime import datetime
from fastapi import APIRouter, Request, Form, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from core.db import shipment_collection  # MongoDB collection

router = APIRouter()
templates = Jinja2Templates(directory="templates")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")


def get_current_user_email(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None


@router.get("/admin/shipments/create", response_class=HTMLResponse)
async def create_shipment_form(request: Request):
    message = request.cookies.get("message")
    response = templates.TemplateResponse("create_shipment.html", {"request": request, "message": message})
    if message:
        response.delete_cookie("message")
    return response


@router.post("/admin/shipments/create", response_class=HTMLResponse)
async def create_shipment(
    request: Request,
    shipmentNumber: str = Form(...),
    route: str = Form(...),
    device: str = Form(...),
    poNumber: int = Form(...),
    ndcNumber: int = Form(...),
    serialNumber: int = Form(...),
    goodsType: str = Form(...),
    deliveryDate: str = Form(...),
    deliveryNumber: int = Form(...),
    batchId: str = Form(...),
    shipmentDesc: str = Form(...)
):
    user_email = get_current_user_email(request)
    if not user_email:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    try:
        delivery_date_obj = datetime.strptime(deliveryDate, "%Y-%m-%d").date()
        delivery_datetime = datetime.combine(delivery_date_obj, datetime.min.time())
    except ValueError:
        return templates.TemplateResponse("create_shipment.html", {
            "request": request,
            "error": "Invalid date format. Use YYYY-MM-DD."
        })

    shipment_data = {
        "shipmentNumber": shipmentNumber,
        "route": route,
        "device": device,
        "poNumber": poNumber,
        "ndcNumber": ndcNumber,
        "serialNumber": serialNumber,
        "goodsType": goodsType,
        "deliveryDate": delivery_datetime,
        "deliveryNumber": deliveryNumber,
        "batchId": batchId,
        "shipmentDesc": shipmentDesc,
        "createdBy": user_email,
        "createdAt": datetime.utcnow()
    }

    shipment_collection.insert_one(shipment_data)

    response = RedirectResponse(url="/admin/shipments/create", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie("message", "Shipment created successfully!", max_age=5)
    return response


# New route: View all shipments
@router.get("/admin/shipments", response_class=HTMLResponse)
async def view_shipments(request: Request):
    user_email = get_current_user_email(request)
    if not user_email:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    shipments = list(shipment_collection.find())
    for shipment in shipments:
        # Convert MongoDB ObjectId to string and datetime to date string for rendering
        shipment["_id"] = str(shipment["_id"])
        if isinstance(shipment.get("deliveryDate"), datetime):
            shipment["deliveryDate"] = shipment["deliveryDate"].strftime("%Y-%m-%d")
        if isinstance(shipment.get("createdAt"), datetime):
            shipment["createdAt"] = shipment["createdAt"].strftime("%Y-%m-%d %H:%M")

    return templates.TemplateResponse("shipment_details.html", {
        "request": request,
        "shipments": shipments
    })

@router.get("/admin/shipments", response_class=HTMLResponse)
async def view_shipments(request: Request):
    user_email = get_current_user_email(request)
    if not user_email:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)

    shipments = list(shipment_collection.find())

    for shipment in shipments:
        shipment["_id"] = str(shipment["_id"])

        delivery_date = shipment.get("deliveryDate")
        created_at = shipment.get("createdAt")

        if isinstance(delivery_date, datetime):
            shipment["deliveryDate"] = delivery_date.strftime("%Y-%m-%d")
        elif isinstance(delivery_date, str):
            shipment["deliveryDate"] = delivery_date  # keep as is

        if isinstance(created_at, datetime):
            shipment["createdAt"] = created_at.strftime("%Y-%m-%d %H:%M")
        elif isinstance(created_at, str):
            shipment["createdAt"] = created_at  # keep as is

    return templates.TemplateResponse("shipment_details.html", {
        "request": request,
        "shipments": shipments
    })