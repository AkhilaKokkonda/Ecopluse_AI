
from typing import Literal

from pydantic import BaseModel, Field


IssueCategory = Literal[
    "Water Leakage",
    "Overflowing Tank",
    "Electricity Wastage",
    "Lighting or Fan Left On",
    "Waste Management",
    "Single-Use Plastic",
    "Other Sustainability Issue",
]

IssueStatus = Literal[
    "Reported",
    "Acknowledged",
    "In Progress",
    "Resolved",
    "Reopened",
]


class IssueCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    category: IssueCategory | None = None
    building: str = Field(min_length=1, max_length=120)
    location_details: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=5, max_length=2000)

    severity: int = Field(default=3, ge=1, le=5)
    safety_risk: int = Field(default=1, ge=1, le=5)
    near_electrical: bool = False
    estimated_resource_loss: float = Field(default=0, ge=0, le=1_000_000)
    unresolved_hours: float = Field(default=0, ge=0, le=1_000_000)

    reporter_name: str = Field(default="", max_length=120)
    reporter_contact: str = Field(default="", max_length=120)


class StatusUpdate(BaseModel):
    status: IssueStatus
    notes: str = Field(default="", max_length=1000)


class RepairVerificationCreate(BaseModel):
    repair_action: str = Field(min_length=3, max_length=500)
    completion_notes: str = Field(default="", max_length=1500)
    estimated_repair_cost: float = Field(default=0, ge=0, le=1_000_000)
    confirmed: bool = False


class LocationCreate(BaseModel):
    building_name: str = Field(min_length=1, max_length=120)
    location_name: str = Field(min_length=1, max_length=120)
    location_details: str = Field(default="", max_length=300)


class WaterSimulation(BaseModel):
    leakage_litres_per_hour: float = Field(default=5, ge=0, le=100_000)
    hours_avoided: float = Field(default=24, ge=0, le=8760)


class ElectricitySimulation(BaseModel):
    power_kw_per_device: float = Field(default=0.5, ge=0, le=100_000)
    device_count: int = Field(default=1, ge=0, le=100_000)
    hours_avoided: float = Field(default=1, ge=0, le=8760)
    tariff_per_kwh: float = Field(default=8, ge=0, le=100_000)
    emission_factor: float = Field(default=0.7, ge=0, le=100)


class StaffAssignment(BaseModel):
    assigned_staff: str = Field(min_length=2, max_length=120)
    notes: str = Field(default="", max_length=1000)

class PlasticSimulation(BaseModel):
    items_avoided: int = Field(ge=0, le=10_000_000)
