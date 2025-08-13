const API_BASE = "/api";

const datePicker = document.getElementById("datePicker");
const dateTitle = document.getElementById("dateTitle");
const prevDayBtn = document.getElementById("prevDay");
const nextDayBtn = document.getElementById("nextDay");
const todayBtn = document.getElementById("todayBtn");
const addEventBtn = document.getElementById("addEventBtn");
const hoursEl = document.getElementById("hours");
const timelineEl = document.getElementById("timeline");
const gridScroll = document.getElementById("gridScroll");

const modal = document.getElementById("eventModal");
const modalTitle = document.getElementById("modalTitle");
const eventForm = document.getElementById("eventForm");
const eventIdInput = document.getElementById("eventId");
const titleInput = document.getElementById("titleInput");
const descInput = document.getElementById("descInput");
const dateInput = document.getElementById("dateInput");
const startInput = document.getElementById("startInput");
const endInput = document.getElementById("endInput");
const saveBtn = document.getElementById("saveBtn");
const deleteBtn = document.getElementById("deleteBtn");
const cancelBtn = document.getElementById("cancelBtn");

function pad(n) { return String(n).padStart(2, "0"); }
function minutesToTime(mins) { const h = Math.floor(mins/60); const m = mins % 60; return `${pad(h)}:${pad(m)}`; }
function timeToMinutes(t) { const [h,m] = t.split(":").map(Number); return h*60 + m; }
function formatDateHuman(d) { return d.toLocaleDateString(undefined, { weekday: "long", year: "numeric", month: "long", day: "numeric" }); }
function toISODate(d) { const tzOffset = d.getTimezoneOffset()*60000; const local = new Date(d.getTime()-tzOffset); return local.toISOString().slice(0,10); }
function fromISODate(s) { const [y,m,da] = s.split("-").map(Number); return new Date(y, m-1, da); }

function ensureFullHeight() {
	// Set fixed min-height to 1440px (1px per minute) so we can scroll the whole day
	timelineEl.style.minHeight = `${24*60}px`;
}

// Build hour grid
function buildGrid() {
	hoursEl.innerHTML = "";
	timelineEl.innerHTML = "";
	ensureFullHeight();
	for (let h=0; h<24; h++) {
		const hour = document.createElement("div");
		hour.className = "hour-row";
		const label = document.createElement("div");
		label.className = "hour-label";
		label.textContent = `${pad(h)}:00`;
		hour.appendChild(label);
		hoursEl.appendChild(hour);

		const row = document.createElement("div");
		row.className = "hour-row";
		row.dataset.hour = h;
		row.addEventListener("dblclick", () => {
			const dateStr = datePicker.value;
			openModal({ id: "", title: "", description: "", date: dateStr, start_minutes: h*60, end_minutes: Math.min(1440, h*60 + 60) });
		});
		timelineEl.appendChild(row);
	}
}

function setNowLine(activeDateISO) {
	const now = new Date();
	const isToday = toISODate(now) === activeDateISO;
	[...timelineEl.querySelectorAll('.now-line,.now-badge')].forEach(n => n.remove());
	if (!isToday) return;
	const mins = Math.max(0, Math.min(1439, now.getHours()*60 + now.getMinutes()));
	const y = mins; // 1px per minute mapping
	const line = document.createElement("div");
	line.className = "now-line";
	line.style.top = `${y}px`;
	const badge = document.createElement("div");
	badge.className = "now-badge";
	badge.style.top = `${y}px`;
	badge.textContent = minutesToTime(mins);
	timelineEl.appendChild(line);
	timelineEl.appendChild(badge);
}

async function fetchDay(dateISO) {
	const res = await fetch(`${API_BASE}/day/${dateISO}`);
	if (!res.ok) throw new Error("Failed to load day");
	return res.json();
}

function renderEvents(items) {
	[...timelineEl.querySelectorAll('.event')].forEach(n => n.remove());
	items.forEach(item => {
		const top = Math.max(0, Math.min(1440, item.start_minutes));
		const height = Math.max(10, Math.min(1440 - top, item.end_minutes - item.start_minutes));
		const el = document.createElement('div');
		el.className = 'event';
		el.style.top = `${top}px`;
		el.style.height = `${height}px`;
		el.innerHTML = `<div class="title"></div><div class="time"></div>`;
		el.querySelector('.title').textContent = item.title;
		el.querySelector('.time').textContent = `${minutesToTime(item.start_minutes)} - ${minutesToTime(item.end_minutes)}`;
		el.title = item.description || '';
		el.addEventListener('click', () => openModal(item));
		timelineEl.appendChild(el);
	});
}

async function load(dateISO, opts={}) {
	datePicker.value = dateISO;
	dateTitle.textContent = formatDateHuman(fromISODate(dateISO));
	buildGrid();
	const items = await fetchDay(dateISO);
	renderEvents(items);
	setNowLine(dateISO);
	if (opts.scrollToNow) {
		const now = new Date();
		if (toISODate(now) === dateISO) {
			const y = (now.getHours()*60 + now.getMinutes()) - 120; // center slightly above
			gridScroll.scrollTo({ top: Math.max(0, y), behavior: 'smooth' });
		} else {
			gridScroll.scrollTo({ top: 0 });
		}
	}
}

function openModal(item) {
	modal.classList.remove('hidden');
	modalTitle.textContent = item.id ? 'Edit Event' : 'Add Event';
	eventIdInput.value = item.id || '';
	titleInput.value = item.title || '';
	descInput.value = item.description || '';
	dateInput.value = item.date || datePicker.value;
	startInput.value = minutesToTime(item.start_minutes || 0);
	endInput.value = minutesToTime(item.end_minutes || Math.min(1440, (item.start_minutes||0)+60));
	deleteBtn.classList.toggle('hidden', !item.id);
}

function closeModal() { modal.classList.add('hidden'); }

cancelBtn.addEventListener('click', closeModal);
modal.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });

addEventBtn.addEventListener('click', () => {
	openModal({ id: '', title: '', description: '', date: datePicker.value, start_minutes: 9*60, end_minutes: 10*60 });
});

prevDayBtn.addEventListener('click', () => {
	const d = fromISODate(datePicker.value); d.setDate(d.getDate()-1); load(toISODate(d), { scrollToNow: true });
});
nextDayBtn.addEventListener('click', () => {
	const d = fromISODate(datePicker.value); d.setDate(d.getDate()+1); load(toISODate(d), { scrollToNow: true });
});
todayBtn.addEventListener('click', () => load(toISODate(new Date()), { scrollToNow: true }));

datePicker.addEventListener('change', () => load(datePicker.value, { scrollToNow: true }));

// Form submit

eventForm.addEventListener('submit', async (e) => {
	e.preventDefault();
	const id = eventIdInput.value.trim();
	const payload = {
		title: titleInput.value.trim(),
		description: descInput.value.trim() || null,
		date: dateInput.value,
		start_minutes: timeToMinutes(startInput.value),
		end_minutes: timeToMinutes(endInput.value)
	};
	if (payload.end_minutes <= payload.start_minutes) {
		alert('End time must be after start time');
		return;
	}
	try {
		if (id) {
			const res = await fetch(`${API_BASE}/item/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
			if (!res.ok) throw new Error(await res.text());
		} else {
			const res = await fetch(`${API_BASE}/item`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
			if (!res.ok) throw new Error(await res.text());
		}
		closeModal();
		await load(datePicker.value, { scrollToNow: true });
	} catch (err) {
		console.error(err);
		alert('Failed to save event');
	}
});

// Delete

deleteBtn.addEventListener('click', async () => {
	const id = eventIdInput.value.trim();
	if (!id) return;
	if (!confirm('Delete this event?')) return;
	try {
		const res = await fetch(`${API_BASE}/item/${id}`, { method: 'DELETE' });
		if (!res.ok) throw new Error(await res.text());
		closeModal();
		await load(datePicker.value, { scrollToNow: true });
	} catch (err) {
		console.error(err);
		alert('Failed to delete event');
	}
});

// Initialize
(function init(){
	const today = new Date();
	load(toISODate(today), { scrollToNow: true });
	setInterval(() => setNowLine(datePicker.value), 60*1000);
})(); 