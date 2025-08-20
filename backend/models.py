from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ScheduleItemBase(BaseModel):
	title: str = Field(min_length=1, max_length=200)
	description: Optional[str] = Field(default=None, max_length=2000)
	# Minutes from start of day: 0..1440
	start_minutes: int = Field(ge=0, le=1440)
	end_minutes: int = Field(ge=0, le=1440)
	# Date in YYYY-MM-DD
	date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")

	@field_validator("end_minutes")
	@classmethod
	def validate_time_range(cls, end_minutes: int, info):
		start_minutes = info.data.get("start_minutes")
		if start_minutes is not None and not (0 <= start_minutes < end_minutes <= 1440):
			raise ValueError("start_minutes must be < end_minutes and both within 0..1440")
		return end_minutes


class ScheduleItemCreate(ScheduleItemBase):
	pass


class ScheduleItemUpdate(BaseModel):
	title: Optional[str] = Field(default=None, min_length=1, max_length=200)
	description: Optional[str] = Field(default=None, max_length=2000)
	start_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
	end_minutes: Optional[int] = Field(default=None, ge=0, le=1440)
	date: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")

	@field_validator("end_minutes")
	@classmethod
	def validate_time_range_update(cls, end_minutes: Optional[int], info):
		start_minutes = info.data.get("start_minutes")
		# Only validate when both are present; full validation happens in storage as well
		if end_minutes is not None and start_minutes is not None:
			if not (0 <= start_minutes < end_minutes <= 1440):
				raise ValueError("start_minutes must be < end_minutes and both within 0..1440")
		return end_minutes


class ScheduleItem(ScheduleItemBase):
	id: str 