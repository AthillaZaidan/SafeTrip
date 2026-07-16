from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel, Field, model_validator


class SearchAttributes(BaseModel):
    time_window_start: Optional[datetime.datetime] = None
    time_window_end: Optional[datetime.datetime] = None
    location: str = ""
    upper_clothing: str = ""
    lower_clothing: str = ""
    direction: str = ""
    event: str = ""
    camera_ids: list[str] = Field(default_factory=list)
    accessories: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_time_window(self):
        if (
            self.time_window_start is not None
            and self.time_window_end is not None
            and self.time_window_end < self.time_window_start
        ):
            raise ValueError("time_window_end must not be before time_window_start")
        return self


class ReportCreate(BaseModel):
    reporter_type: str = "passenger"
    time_window_start: Optional[datetime.datetime] = None
    time_window_end: Optional[datetime.datetime] = None
    location: str = ""
    description: str = ""
    direction: str = ""
    image_url: str = ""

    @model_validator(mode="after")
    def validate_time_window(self):
        if (
            self.time_window_start is not None
            and self.time_window_end is not None
            and self.time_window_end < self.time_window_start
        ):
            raise ValueError("time_window_end must not be before time_window_start")
        return self


class ReportUpdate(BaseModel):
    status: Optional[str] = None


class AttributeUpdate(BaseModel):
    attributes: SearchAttributes


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
    attributes: dict = Field(default_factory=dict)
    image_url: str = ""
