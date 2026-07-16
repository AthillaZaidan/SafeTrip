from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    reporter_type: str = "passenger"
    time_window_start: Optional[datetime.datetime] = None
    time_window_end: Optional[datetime.datetime] = None
    location: str = ""
    description: str = ""
    direction: str = ""
    image_url: str = ""


class ReportUpdate(BaseModel):
    status: Optional[str] = None


class AttributeUpdate(BaseModel):
    attributes: dict


class ReportList(BaseModel):
    report_id: str
    reporter_type: str
    location: str
    description: str = ""
    status: str = "submitted"
    created_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


class ReportDetail(ReportList):
    time_window_start: Optional[datetime.datetime] = None
    time_window_end: Optional[datetime.datetime] = None
    direction: str = ""
    attributes: dict = {}
    image_url: str = ""
