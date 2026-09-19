export const API_BASE = import.meta.env.VITE_API_URL ?? (import.meta.env.PROD ? '' : '/api');

const handleJsonResponse = async (response) => {
  const text = await response.text();
  let payload = {};
  try {
    payload = text ? JSON.parse(text) : {};
  } catch (error) {
    payload = { error: text || 'Request failed.' };
  }

  if (!response.ok) {
    throw new Error(payload.error || 'Request failed.');
  }

  return payload;
};

export const getSchedule = (patients) =>
  fetch(`${API_BASE}/schedule`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patients }),
  }).then(handleJsonResponse);

export const addEmergency = (current_schedule, emergency_patient) =>
  fetch(`${API_BASE}/emergency`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ current_schedule, emergency_patient }),
  }).then(handleJsonResponse);

export const addPatient = (patient) =>
  fetch(`${API_BASE}/patients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patient),
  }).then(handleJsonResponse);

export const deletePatient = (patientId) =>
  fetch(`${API_BASE}/patients/${patientId}`, {
    method: 'DELETE',
  }).then(handleJsonResponse);

export const getResources = () =>
  Promise.all([
    fetch(`${API_BASE}/rooms`).then(handleJsonResponse),
    fetch(`${API_BASE}/surgeons`).then(handleJsonResponse),
  ]).then(([rooms, surgeons]) => ({ rooms: rooms.rooms || [], surgeons: surgeons.surgeons || [] }));
