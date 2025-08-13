from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from .models import ScheduleItem, ScheduleItemCreate, ScheduleItemUpdate
from .storage import FileStorage


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"
DATA_DIR = ROOT_DIR / "data"

app = FastAPI(title="Schedule API", version="0.1.0")

# Allow local frontend and webview
app.add_middleware(
	CORSMiddleware,
	allow_origins=["*"],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)

storage = FileStorage(DATA_DIR)


@app.post("/api/item", response_model=ScheduleItem)
async def create_item(item: ScheduleItemCreate) -> ScheduleItem:
	try:
		return storage.create_item(item)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/item/{item_id}", response_model=ScheduleItem)
async def get_item(item_id: str) -> ScheduleItem:
	item = storage.get_item(item_id)
	if not item:
		raise HTTPException(status_code=404, detail="Item not found")
	return item


@app.put("/api/item/{item_id}", response_model=ScheduleItem)
async def update_item(item_id: str, updates: ScheduleItemUpdate) -> ScheduleItem:
	try:
		item = storage.update_item(item_id, updates)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))
	if not item:
		raise HTTPException(status_code=404, detail="Item not found")
	return item


@app.delete("/api/item/{item_id}")
async def delete_item(item_id: str) -> Dict[str, bool]:
	ok = storage.delete_item(item_id)
	if not ok:
		raise HTTPException(status_code=404, detail="Item not found")
	return {"ok": True}


@app.get("/api/day/{date_str}", response_model=List[ScheduleItem])
async def list_day(date_str: str) -> List[ScheduleItem]:
	return storage.list_day(date_str)


@app.get("/api/range")
async def list_range(start: str, end: str) -> Dict[str, List[ScheduleItem]]:
	try:
		return storage.list_range(start, end)
	except ValueError as e:
		raise HTTPException(status_code=400, detail=str(e))


# Serve frontend
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend") 