# Operation Room Scheduling System

A full-stack web application for organizing hospital operating-room procedures by urgency, wait time, duration, and available resources.

The system provides a central dashboard where staff can add procedures, assign preferred surgeons and operating rooms, specify equipment requirements, view a date-based schedule, and handle emergency cases.

## Features

- Schedule a new procedure with patient and medical-record information
- Select procedure type, duration, urgency, and priority weight
- Choose a preferred date and start time
- Assign a preferred surgeon and operating room, or allow automatic assignment
- Record clinical notes and required equipment
- View procedures across multiple operating rooms
- Navigate schedules by previous date, next date, or selected date
- Add emergency procedures
- Remove procedures from the schedule
- Store patient and resource data in a local SQLite database
- Display loading, success, and validation error messages

## Priority Levels

The application supports four urgency levels:

| Level | Purpose |
|---|---|
| Routine | Standard non-urgent procedure |
| Urgent | Procedure requiring earlier attention |
| Critical | High-priority procedure |
| Emergency | Unexpected procedure requiring immediate queue priority |

Priority is calculated from the patient’s urgency, priority weight (`k`), and time spent waiting.

## Emergency Handling

When an emergency procedure is added:

1. The currently active procedure remains in place.
2. The emergency procedure is placed at the front of the waiting queue.
3. Remaining waiting procedures are reordered using the scheduling logic.

This approach avoids interrupting an in-progress operation while responding to urgent demand.

## Technology Stack

### Frontend

- React 18
- Vite
- Tailwind CSS
- JavaScript

### Backend

- Python
- Flask
- Flask-CORS
- Flask-SocketIO
- SQLite

## Project Structure

```text
Operation room scheduling/
├── backend/
│   ├── app.py             # Flask API routes and server startup
│   ├── db.py              # SQLite setup and database operations
│   ├── scheduler.py       # Priority and emergency scheduling logic
│   └── seed.py            # Default rooms, surgeons, and sample data
├── database/
│   └── or_schedule.db     # Local SQLite database, created automatically
├── frontend/
│   ├── src/
│   │   ├── App.jsx        # Main application layout and date management
│   │   ├── PatientForm.jsx# Procedure and emergency form
│   │   ├── ScheduleGrid.jsx # Operating-room schedule display
│   │   └── api.js         # Frontend API requests
│   ├── package.json
│   └── vite.config.js
├── requirements.txt
└── README.md
```

## Architecture

The React frontend runs on port `3000`. Vite forwards requests beginning with `/api` to the Flask backend on port `5000`.

```text
React frontend → /api proxy → Flask API → SQLite database
```

The frontend manages the dashboard, user inputs, date navigation, schedule display, and API calls.

The backend validates requests, stores data, retrieves resources, generates procedure order, and returns schedule information.

## Installation

### Prerequisites

Install the following before starting:

- Python 3
- Node.js and npm
- Git

### Backend setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cd backend
python app.py
```

The backend starts at:

```text
http://localhost:5000
```

### Frontend setup

Open a second terminal from the project root:

```powershell
cd frontend
npm install
npm run dev
```

Open the application in a browser:

```text
http://localhost:3000
```

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/patients` | Retrieve all saved procedures |
| `POST` | `/patients` | Create a new procedure |
| `DELETE` | `/patients/<id>` | Remove a procedure |
| `POST` | `/schedule` | Generate a priority-based schedule |
| `POST` | `/emergency` | Add and prioritize an emergency procedure |
| `GET` | `/rooms` | Retrieve operating-room details |
| `GET` | `/surgeons` | Retrieve surgeon details |

## Database

The SQLite database contains three main tables:

- `patients` — patient, procedure, priority, timing, room, surgeon, notes, and equipment data
- `rooms` — operating-room names and equipment descriptions
- `surgeons` — surgeon names and availability information

The database is initialized automatically when the backend starts. If it is empty, default sample data is seeded.

To reset sample data manually:

```powershell
cd backend
python seed.py
```

> Warning: running the seed script deletes existing patients, rooms, and surgeons before adding the default records.

## Testing Checklist

Use a future date in the date picker, such as `2026-10-15`, then test:

- Select a date and verify the heading and form use that date.
- Add a routine procedure and confirm it appears in the schedule.
- Add urgent and critical procedures and check their priority ordering.
- Add an emergency procedure and verify the queue updates.
- Remove a procedure and confirm it disappears from the schedule.
- Submit without a patient name and confirm validation is displayed.
- Submit without a medical ID and confirm validation is displayed.
- Submit a duration of zero and confirm the backend rejects it.
- Test auto-assignment and preferred room/surgeon assignment.
- Select equipment requirements and confirm they are saved with the procedure.

## Current Limitations

This project is a scheduling prototype. It stores preferred time and resource information, but it does not yet fully calculate exact conflict-free start and end times for every procedure based on room occupancy, surgeon availability, and equipment availability.

Future improvements could include:

- Real-time schedule updates through Socket.IO on the frontend
- Exact time-slot calculations and visual placement in the timeline
- Room, surgeon, and equipment conflict detection
- User authentication and role-based access
- Search and filtering
- Edit procedure details
- Data export and reporting
- Automated frontend and backend tests
- Deployment with a managed production database

## Development History

The project was initialized locally with Git, committed, connected to GitHub, and merged with the remote `main` branch.

Repository:

https://github.com/Shrihare7734/Operation-Room-Scheduling

## License

This project is intended for educational and prototype use.
