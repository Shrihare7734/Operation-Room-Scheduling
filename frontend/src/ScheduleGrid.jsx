const direnessColors = {
  routine: 'bg-blue-500',
  urgent: 'bg-orange-500',
  critical: 'bg-red-500',
  emergency: 'bg-red-700 ring-2 ring-red-300',
};

const formatTime = (value) => new Date(value).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
const formatWindow = (patient) => `${formatTime(patient.earliest_start_time)} - ${formatTime(patient.latest_end_time)}`;

export default function ScheduleGrid({ schedule, rooms, onRemove }) {
  const roomList = rooms.length ? rooms : [{ id: 0, name: 'OR-1', equipment: 'General Surgery' }];
  const scheduledCount = schedule.filter((patient) => patient.status !== 'unschedulable').length;
  const grouped = roomList.map((room) => ({
    room,
    procedures: schedule.filter((patient) => patient.room_id === room.id),
  }));

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <div><h2 className="text-xl font-bold text-slate-900">Multi-room timeline</h2><p className="text-sm text-slate-500">6:00 AM to 6:00 PM • {scheduledCount} scheduled procedures</p></div>
        <span className={`rounded-full px-3 py-1 text-xs font-bold ${schedule.some((patient) => patient.status === 'unschedulable') ? 'bg-red-50 text-red-700' : 'bg-emerald-50 text-emerald-700'}`}>{schedule.some((patient) => patient.status === 'unschedulable') ? 'Window conflicts' : 'No overlaps'}</span>
      </div>
      <div className="mb-2 grid grid-cols-[150px_repeat(7,minmax(75px,1fr))] border-b border-slate-200 text-[11px] font-semibold text-slate-400">
        <div className="p-2">Operating room</div>
        {['6 AM', '8 AM', '10 AM', '12 PM', '2 PM', '4 PM', '6 PM'].map((time) => <div key={time} className="border-l border-slate-100 p-2">{time}</div>)}
      </div>
      <div className="space-y-3">
        {grouped.map(({ room, procedures }) => (
          <div key={room.id} className="grid min-h-[108px] grid-cols-[150px_minmax(0,1fr)] rounded-lg border border-slate-200 bg-slate-50">
            <div className="border-r border-slate-200 p-3"><p className="font-bold text-slate-800">{room.name}</p><p className="mt-1 text-xs text-slate-500">{room.equipment}</p><p className="mt-3 text-[11px] text-emerald-600">Available slots shown</p></div>
            <div className="relative grid grid-cols-6 bg-white">
              {Array.from({ length: 6 }, (_, index) => <div key={index} className="border-l border-dashed border-slate-200" />)}
              {procedures.map((patient) => (
                <div key={patient.id} className={`absolute left-1 top-2 w-[calc(33.33%-8px)] min-w-[145px] rounded-md p-2 text-white shadow-sm ${direnessColors[patient.direness] || direnessColors.routine}`}>
                  <div className="flex items-start justify-between gap-1"><p className="truncate text-xs font-bold">{patient.name}</p><button type="button" title="Remove operation" onClick={() => onRemove(patient.id)} className="text-xs font-bold opacity-90 hover:opacity-100">×</button></div>
                  <p className="mt-1 truncate text-[11px]">{patient.procedure_type || 'General Surgery'}</p>
                  <p className="mt-1 text-[10px]">{patient.scheduled_start ? `${formatTime(patient.scheduled_start)} - ${formatTime(patient.scheduled_end)}` : 'Unschedulable'} • {patient.surgeon_name || 'Unassigned'}</p>
                  <p className="text-[10px]">Window: {formatWindow(patient)}</p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-5 border-t border-slate-200 pt-4"><h3 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">Scheduled operations</h3><div className="max-h-64 space-y-2 overflow-y-auto">{schedule.map((patient) => <div key={patient.id} className={`flex items-center justify-between gap-3 rounded-md border px-3 py-2 ${patient.status === 'unschedulable' ? 'border-red-300 bg-red-50' : 'border-slate-200'}`}><div className="min-w-0"><p className="truncate text-sm font-semibold">{patient.name}</p><p className="text-xs text-slate-500">{patient.scheduled_start ? `${formatTime(patient.scheduled_start)} - ${formatTime(patient.scheduled_end)}` : patient.schedule_error}</p><p className="text-xs text-slate-500">Window: {formatWindow(patient)} • {patient.room_name || 'Unassigned'}</p></div><button type="button" onClick={() => onRemove(patient.id)} className="shrink-0 rounded-md border border-red-200 px-2.5 py-1 text-xs font-semibold text-red-700 hover:bg-red-50">Remove</button></div>)}</div></div>
    </section>
  );
}
