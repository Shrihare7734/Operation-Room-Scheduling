import { useEffect, useState } from 'react';
import { API_BASE, addPatient } from './api';

const equipmentOptions = ['Laparoscopy set', 'Ultrasound machine', 'Orthopedic drill', 'ECG monitor', 'Enhanced surgical lights'];

const makeForm = (selectedDate) => ({
  name: '', medical_id: '', procedure_type: 'General Surgery', direness: 'routine', k: 1,
  earliest_start_time: '08:00', latest_end_time: '12:00',
  estimated_min_duration: 30, estimated_max_duration: 60,
  preferred_date: selectedDate, preferred_start_time: '08:00',
  notes: '', surgeon_id: '', room_id: '', equipment: [],
});

export default function PatientForm({ currentSchedule, selectedDate, resources, reloadSchedule }) {
  const [form, setForm] = useState(() => makeForm(selectedDate));
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  useEffect(() => {
    setForm(makeForm(selectedDate));
  }, [selectedDate]);

  const handleChange = (event) => {
    const { name, value } = event.target;
    setForm((previous) => ({ ...previous, [name]: ['duration', 'k', 'surgeon_id', 'room_id'].includes(name) ? value : value }));
  };

  const toggleEquipment = (item) => setForm((previous) => ({ ...previous, equipment: previous.equipment.includes(item) ? previous.equipment.filter((entry) => entry !== item) : [...previous.equipment, item] }));

  const windowStart = new Date(`${selectedDate}T${form.earliest_start_time}`);
  const windowEnd = new Date(`${selectedDate}T${form.latest_end_time}`);
  const windowMinutes = Math.round((windowEnd - windowStart) / 60000);
  const windowValid = Number.isFinite(windowMinutes) && windowMinutes >= 30;
  const flexibility = windowMinutes > 240 ? 'FLEXIBLE' : windowMinutes >= 120 ? 'MODERATE' : 'TIGHT';

  const submit = async (emergency = false) => {
    setError('');
    try {
      if (!windowValid || windowEnd <= windowStart) throw new Error(windowEnd <= windowStart ? 'Latest end time must be after earliest start time.' : 'Time window must be at least 30 minutes.');
      const earliestDateTime = `${selectedDate}T${form.earliest_start_time}:00`;
      const latestDateTime = `${selectedDate}T${form.latest_end_time}:00`;
      const payload = { ...form, earliest_start_time: earliestDateTime, latest_end_time: latestDateTime, preferred_date: selectedDate, duration: Number(form.estimated_min_duration) || 30, estimated_min_duration: Number(form.estimated_min_duration) || 30, estimated_max_duration: Number(form.estimated_max_duration) || 60, k: Number(form.k), status: emergency ? 'emergency' : 'waiting', equipment: form.equipment.join(', '), arrival_time: earliestDateTime };
      const response = emergency ? await fetch(`${API_BASE}/emergency`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ current_schedule: currentSchedule, emergency_patient: payload }) }).then((result) => result.json()) : await addPatient(payload);
      if (response.error) throw new Error(response.error);
      await reloadSchedule();
      setForm(makeForm(selectedDate));
      setMessage(emergency ? 'Emergency received and queue updated.' : 'Procedure scheduled successfully.');
    } catch (err) { setError(err.message || 'Unable to schedule procedure.'); }
  };

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-4"><h2 className="text-xl font-bold text-slate-900">Schedule procedure</h2><p className="text-sm text-slate-500">For {selectedDate}</p></div>
      <div className="space-y-5">
        <fieldset><legend className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">Patient information</legend><div className="grid gap-3 sm:grid-cols-2"><label className="field">Patient name *<input name="name" value={form.name} onChange={handleChange} placeholder="Full name" /></label><label className="field">Medical ID *<input name="medical_id" value={form.medical_id} onChange={handleChange} placeholder="MRN-0000" /></label><label className="field sm:col-span-2">Procedure type<select name="procedure_type" value={form.procedure_type} onChange={handleChange}>{['Cardiac Surgery', 'Orthopedic', 'General Surgery', 'Laparoscopy', 'Trauma', 'Other'].map((item) => <option key={item}>{item}</option>)}</select></label></div></fieldset>
        <fieldset><legend className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">Scheduling window</legend><div className="grid gap-3 sm:grid-cols-2"><label className="field">Earliest start *<input type="time" name="earliest_start_time" value={form.earliest_start_time} onChange={handleChange} /><span className="font-normal text-slate-400">Surgery cannot start before this time.</span></label><label className="field">Latest end *<input type="time" name="latest_end_time" value={form.latest_end_time} onChange={handleChange} /><span className="font-normal text-slate-400">Surgery must finish by this time.</span></label><label className="field">Estimated minimum (optional)<input type="number" min="1" name="estimated_min_duration" value={form.estimated_min_duration} onChange={handleChange} /></label><label className="field">Estimated maximum (optional)<input type="number" min="1" name="estimated_max_duration" value={form.estimated_max_duration} onChange={handleChange} /></label><label className="field">Priority level<select name="direness" value={form.direness} onChange={handleChange}><option value="emergency">Emergency</option><option value="critical">Critical</option><option value="urgent">Urgent</option><option value="routine">Routine</option></select></label><label className="field">Priority weight<input type="number" step="0.1" name="k" value={form.k} onChange={handleChange} /></label><label className="field sm:col-span-2">Notes / special requirements<textarea name="notes" value={form.notes} onChange={handleChange} rows="2" placeholder="Equipment, clinical or preparation notes" /></label></div><div className={`mt-3 rounded-md p-3 text-sm ${windowEnd <= windowStart || windowMinutes < 30 ? 'bg-red-50 text-red-700' : windowMinutes < 120 ? 'bg-red-50 text-red-700' : windowMinutes < 240 ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'}`}>{windowEnd <= windowStart ? 'Latest end time must be after earliest start time.' : `Calculated window: ${Math.floor(windowMinutes / 60)}h ${windowMinutes % 60}m • ${flexibility} scheduling`}</div></fieldset>
        <fieldset><legend className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">Surgeon and room assignment</legend><div className="grid gap-3 sm:grid-cols-2"><label className="field">Preferred surgeon<select name="surgeon_id" value={form.surgeon_id} onChange={handleChange}><option value="">Auto assign</option>{resources.surgeons.map((surgeon) => <option key={surgeon.id} value={surgeon.id}>{surgeon.name} • {surgeon.available}</option>)}</select></label><label className="field">Operating room<select name="room_id" value={form.room_id} onChange={handleChange}><option value="">Auto assign</option>{resources.rooms.map((room) => <option key={room.id} value={room.id}>{room.name} • {room.equipment}</option>)}</select></label></div></fieldset>
        <fieldset><legend className="mb-3 text-xs font-bold uppercase tracking-wide text-slate-500">Equipment requirements</legend><div className="grid gap-2 sm:grid-cols-2">{equipmentOptions.map((item) => <label key={item} className="flex items-center gap-2 text-sm text-slate-700"><input type="checkbox" checked={form.equipment.includes(item)} onChange={() => toggleEquipment(item)} />{item}</label>)}</div></fieldset>
      </div>
      {error && <p className="mt-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</p>}{message && <p className="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-emerald-700">{message}</p>}
      <div className="mt-5 grid gap-2 sm:grid-cols-2"><button type="button" onClick={() => submit(false)} className="rounded-md bg-blue-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-blue-700">Schedule procedure</button><button type="button" onClick={() => submit(true)} className="rounded-md bg-red-600 px-4 py-2.5 text-sm font-bold text-white hover:bg-red-700">Add as emergency</button><button type="button" onClick={() => { setForm(makeForm(selectedDate)); setError(''); setMessage(''); }} className="rounded-md border border-slate-300 px-4 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50">Clear form</button></div>
    </section>
  );
}
