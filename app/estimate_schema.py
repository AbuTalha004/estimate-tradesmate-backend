
from typing import List
from pydantic import BaseModel, Field, condecimal, constr

class Item(BaseModel):
    description: constr(strip_whitespace=True, min_length=1)
    quantity: int = Field(..., gt=0)
    unit_price: condecimal(gt=0)

    @property
    def total(self) -> float:
        return float(self.quantity * self.unit_price)

class EstimateRequest(BaseModel):
    client_name: str
    job_type: str
    job_description: str
    items: List[Item]
    notes: str | None = ""

class EstimateResponse(BaseModel):
    transcript: str
    parsed_json: EstimateRequest
