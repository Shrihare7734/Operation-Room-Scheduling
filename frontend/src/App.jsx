import { useEffect, useRef, useState } from 'react';
import ScheduleGrid from './ScheduleGrid';
import PatientForm from './PatientForm';
import { deletePatient, getResources } from './api';

const formatDate = (date) => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};
const displayDate = (date) => date.toLocaleDateString(undefined, { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

export default function App() {
  const [schedule, setSchedule] = useState([]);
  const [totalCost, setTotalCost] = useState(0);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [resources, setResources] = useState({ rooms: [], surgeons: [] });
  const [loading, setLoading] = useState(true);
  const dateInputRef = useRef(null);
  const selectedDateValue = formatDate(selectedDate);

  const refreshSchedule = (newSchedule, cost) => {
    setSchedule(newSchedule || []);
    setTotalCost(cost || 0);
  };

  const loadSchedule = async (dateValue = selectedDateValue) => {
    const patientsResponse = await fetch('/api/patients');
    const data = await patientsResponse.json();
    const scheduleResponse = await fetch('/api/schedule', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ patients: data.patients || [], date: dateValue }),
    });
    const scheduleData = await scheduleResponse.json();
    refreshSchedule(scheduleData.schedule, scheduleData.total_cost);
  };

  const removeOperation = async (patientId) => {
    await deletePatient(patientId);
    await loadSchedule();
  };

  useEffect(() => {
    setLoading(true);
    Promise.all([loadSchedule(selectedDateValue), getResources()])
      .then(([, resourceData]) => setResources(resourceData))
      .catch(() => refreshSchedule([], 0))
      .finally(() => setLoading(false));
  }, [selectedDateValue]);

  const shiftDate = (days) => {
    const next = new Date(selectedDate);
    next.setDate(next.getDate() + days);
    setSelectedDate(next);
  };

  const handleDateInput = (event) => {
    if (!event.target.value) return;
    const [year, month, day] = event.target.value.split('-').map(Number);
    setSelectedDate(new Date(year, month - 1, day));
  };

  const openDatePicker = () => {
    const input = dateInputRef.current;
    if (!input) return;
    if (typeof input.showPicker === 'function') {
      input.showPicker();
      return;
    }
    input.focus();
    input.click();
  };

  return (
    <div className="min-h-screen bg-[#eef4f7] p-4 text-slate-800 md:p-6">
      <div className="mx-auto max-w-[1500px]">
        <header className="mb-4 rounded-2xl bg-[#123047] p-5 text-white shadow-lg">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-cyan-200">Hospital operations control</p>
              <h1 className="mt-1 text-3xl font-bold">Operating room schedule</h1>
              <p className="mt-1 text-sm text-slate-300">{displayDate(selectedDate)}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <button onClick={() => shiftDate(-1)} className="rounded-lg border border-white/20 px-3 py-2 text-sm hover:bg-white/10">&lt; Previous</button>
              <button onClick={() => setSelectedDate(new Date())} className="rounded-lg bg-cyan-400 px-3 py-2 text-sm font-bold text-[#123047]">Today</button>
              <button onClick={() => shiftDate(1)} className="rounded-lg border border-white/20 px-3 py-2 text-sm hover:bg-white/10">Next &gt;</button>
              <button type="button" onClick={openDatePicker} className="rounded-lg border border-white/20 px-3 py-2 text-sm hover:bg-white/10">
                Date picker: {selectedDateValue}
              </button>
              <input
                ref={dateInputRef}
                type="date"
                value={selectedDateValue}
                onChange={handleDateInput}
                aria-label="Choose schedule date"
                tabIndex="-1"
                className="sr-only"
              />
              <span className="rounded-lg bg-white/10 px-3 py-2 text-sm">{schedule.length} cases</span>
            </div>
          </div>
        </header>

        <div className="mb-6 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900">
          <strong>Emergency rule:</strong> When a case arrives unexpectedly, the current procedure stays in place. The emergency patient is placed at the front of the waiting list and the remaining queue is re-ordered without overlap. No fixed emergency time is assumed.
        </div>

        {loading && <div className="mb-4 rounded-lg bg-white px-4 py-3 text-sm text-slate-500 shadow-sm">Refreshing schedule...</div>}
        <div className="grid gap-5 xl:grid-cols-[230px_minmax(0,1fr)_360px]">
          <aside className="space-y-5">
            <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">Available surgeons</h2>
              <div className="space-y-3">
                {resources.surgeons.map((surgeon) => <div key={surgeon.id} className="border-b border-slate-100 pb-2 last:border-0"><p className="text-sm font-semibold">{surgeon.name}</p><p className="text-xs text-emerald-600">Available today</p><p className="text-xs text-slate-500">{surgeon.available}</p></div>)}
              </div>
            </section>
            <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">Schedule alerts</h2>
              <p className="text-sm text-slate-600">{schedule.length ? 'No room overlaps detected.' : 'No procedures scheduled for this date.'}</p>
            </section>
          </aside>
          <ScheduleGrid schedule={schedule} rooms={resources.rooms} totalCost={totalCost} onRemove={removeOperation} />
          <PatientForm
            currentSchedule={schedule}
            refreshSchedule={refreshSchedule}
            setTotalCost={setTotalCost}
            selectedDate={selectedDateValue}
            resources={resources}
            reloadSchedule={loadSchedule}
          />
        </div>
        <section className="mt-5 rounded-xl border border-slate-200 bg-white p-4 shadow-sm"><h2 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">Equipment inventory</h2><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{['Laparoscopy sets', 'Ultrasound machines', 'Orthopedic drills', 'ECG monitors', 'Surgical lights'].map((item) => <div key={item} className="rounded-lg bg-slate-50 p-3"><p className="text-sm font-semibold">{item}</p><p className="mt-1 text-xs text-emerald-600">Available</p></div>)}</div></section>
      </div>
    </div>
  );
}
