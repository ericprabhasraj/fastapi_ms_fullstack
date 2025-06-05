from pydantic import BaseModel, EmailStr, Field
from datetime import date

# Shipment schema
class Shipment(BaseModel):
    shipmentNumber: str
    route: str
    device: str
    poNumber: int
    ndcNumber: int
    serialNumber: int
    goodsType: str
    deliveryDate: date
    deliveryNumber: int
    batchId: str
    shipmentDesc: str

# User schema for validation (for request bodies)
class UserBase(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=6)
