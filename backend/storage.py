from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import date as date_cls, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pydantic import ValidationError

from .models import ScheduleItem, ScheduleItemCreate, ScheduleItemUpdate


@dataclass
class _ScheduleItemRecord:
	id: str
	title: str
	description: Optional[str]
	start_minutes: int
	end_minutes: int
	date: str


class FileStorage:
	def __init__(self, data_dir: Path) -> None:
		self.data_dir = Path(data_dir)
		self.data_dir.mkdir(parents=True, exist_ok=True)
		self.index_file = self.data_dir / "index.json"
		if not self.index_file.exists():
			self._write_json(self.index_file, {})

	@staticmethod
	def _read_json(path: Path):
		if not path.exists():
			return None
		with path.open("r", encoding="utf-8") as f:
			return json.load(f)

	@staticmethod
	def _write_json(path: Path, data) -> None:
		path.parent.mkdir(parents=True, exist_ok=True)
		with path.open("w", encoding="utf-8") as f:
			json.dump(data, f, indent=2)

	def _day_file(self, date_str: str) -> Path:
		return self.data_dir / f"{date_str}.json"

	def _load_index(self) -> Dict[str, str]:
		return self._read_json(self.index_file) or {}

	def _save_index(self, index: Dict[str, str]) -> None:
		self._write_json(self.index_file, index)

	def _load_day_items(self, date_str: str) -> List[Dict]:
		path = self._day_file(date_str)
		return self._read_json(path) or []

	def _save_day_items(self, date_str: str, items: List[Dict]) -> None:
		self._write_json(self._day_file(date_str), items)

	def create_item(self, item: ScheduleItemCreate) -> ScheduleItem:
		# Validate logical time ordering again
		if not (0 <= item.start_minutes < item.end_minutes <= 1440):
			raise ValueError("Invalid time range")
		new_id = str(uuid.uuid4())
		record = _ScheduleItemRecord(
			id=new_id,
			title=item.title,
			description=item.description,
			start_minutes=item.start_minutes,
			end_minutes=item.end_minutes,
			date=item.date,
		)
		items = self._load_day_items(item.date)
		items.append(asdict(record))
		# Sort by start time
		items.sort(key=lambda r: (r.get("start_minutes", 0), r.get("end_minutes", 0)))
		self._save_day_items(item.date, items)
		index = self._load_index()
		index[new_id] = item.date
		self._save_index(index)
		return ScheduleItem(**asdict(record))

	def get_item(self, item_id: str) -> Optional[ScheduleItem]:
		index = self._load_index()
		date_str = index.get(item_id)
		if not date_str:
			return None
		for rec in self._load_day_items(date_str):
			if rec.get("id") == item_id:
				return ScheduleItem(**rec)
		return None

	def update_item(self, item_id: str, updates: ScheduleItemUpdate) -> Optional[ScheduleItem]:
		index = self._load_index()
		current_date = index.get(item_id)
		if not current_date:
			return None
		items = self._load_day_items(current_date)
		updated_rec: Optional[Dict] = None
		for rec in items:
			if rec.get("id") == item_id:
				updated_rec = rec
				break
		if updated_rec is None:
			return None

		# Apply updates
		if updates.title is not None:
			updated_rec["title"] = updates.title
		if updates.description is not None:
			updated_rec["description"] = updates.description
		if updates.start_minutes is not None:
			updated_rec["start_minutes"] = updates.start_minutes
		if updates.end_minutes is not None:
			updated_rec["end_minutes"] = updates.end_minutes
		new_date = updates.date if updates.date is not None else current_date

		# Validate with model
		try:
			ScheduleItem(**{**updated_rec, "date": new_date})
		except ValidationError as e:
			raise ValueError(str(e))

		# If date changed, move record
		if new_date != current_date:
			items = [r for r in items if r.get("id") != item_id]
			self._save_day_items(current_date, items)
			# Append to new date file
			new_items = self._load_day_items(new_date)
			updated_rec["date"] = new_date
			new_items.append(updated_rec)
			new_items.sort(key=lambda r: (r.get("start_minutes", 0), r.get("end_minutes", 0)))
			self._save_day_items(new_date, new_items)
			index[item_id] = new_date
			self._save_index(index)
			return ScheduleItem(**updated_rec)
		else:
			# Save same day
			items.sort(key=lambda r: (r.get("start_minutes", 0), r.get("end_minutes", 0)))
			self._save_day_items(current_date, items)
			return ScheduleItem(**updated_rec)

	def delete_item(self, item_id: str) -> bool:
		index = self._load_index()
		date_str = index.get(item_id)
		if not date_str:
			return False
		items = self._load_day_items(date_str)
		new_items = [r for r in items if r.get("id") != item_id]
		if len(new_items) == len(items):
			return False
		self._save_day_items(date_str, new_items)
		index.pop(item_id, None)
		self._save_index(index)
		return True

	def list_day(self, date_str: str) -> List[ScheduleItem]:
		items = self._load_day_items(date_str)
		return [ScheduleItem(**r) for r in items]

	def list_range(self, start_date: str, end_date: str) -> Dict[str, List[ScheduleItem]]:
		start = date_cls.fromisoformat(start_date)
		end = date_cls.fromisoformat(end_date)
		if end < start:
			raise ValueError("end_date must be >= start_date")
		result: Dict[str, List[ScheduleItem]] = {}
		cursor = start
		while cursor <= end:
			key = cursor.isoformat()
			result[key] = self.list_day(key)
			cursor += timedelta(days=1)
		return result 