const BASE = '/api';

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
  fetch(`${BASE}/schedule`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patients }),
  }).then(handleJsonResponse);

export const addEmergency = (current_schedule, emergency_patient) =>
  fetch(`${BASE}/emergency`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ current_schedule, emergency_patient }),
  }).then(handleJsonResponse);

export const addPatient = (patient) =>
  fetch(`${BASE}/patients`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(patient),
  }).then(handleJsonResponse);

export const deletePatient = (patientId) =>
  fetch(`${BASE}/patients/${patientId}`, {
    method: 'DELETE',
  }).then(handleJsonResponse);

export const getResources = () =>
  Promise.all([
    fetch(`${BASE}/rooms`).then(handleJsonResponse),
    fetch(`${BASE}/surgeons`).then(handleJsonResponse),
  ]).then(([rooms, surgeons]) => ({ rooms: rooms.rooms || [], surgeons: surgeons.surgeons || [] }));
