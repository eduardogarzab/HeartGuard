# HeartGuard

HeartGuard is an AI-powered platform designed to monitor patients at cardiovascular risk in real time.
Its goal is to detect early warning signs of emergencies and trigger timely alerts for medical intervention.

---

## Backend (PostgreSQL with Docker)

A backend service has been added to simplify local development.
This backend uses Docker Compose to run PostgreSQL in a consistent environment for all team members.

### Requirements
- [Docker](https://www.docker.com/get-started) installed
- [Docker Compose](https://docs.docker.com/compose/) available

### How to start the database

1. Navigate to the `backend/` folder:
   ```bash
   cd backend
   ```

2. Start the PostgreSQL container:
   ```bash
   docker compose up -d
   ```

3. Verify that it is running:
   ```bash
   docker ps
   ```

   You should see a container named **`postgres-container`**.

### Default configuration

- **Host:** `localhost`
- **Port:** `5432`
- **Database:** `heartguard`
- **User:** `postgres`
- **Password:** `heartguard1234`

### Connect using psql

You can connect directly to the container with:

```bash
docker exec -it postgres-container psql -U postgres -d heartguard
```

### Data persistence

A Docker volume named **`postgres-data`** is used.
This ensures that your database files are preserved even if the container is stopped or recreated.

---

## Extended Backend (Go + Gin + HTML/CSS/JS)

For the **first project deliverable**, we also added a backend module in **Go** with the following features:

- **Go Backend (Gin framework)** → Exclusive to administrators. Provides login and CRUD operations for patients.
- **PostgreSQL schema (`init.sql`)** → Includes organizations, patients, alerts, predictions, and emergency contacts.
- **Constraint in Postgres** → Guarantees only **one admin per organization**.
- **Frontend views**:
  - `/login` → Login screen for administrators.
  - `/admin` → Admin dashboard for managing patients.

### Frontend Assets
- **HTML**: `templates/login.html`, `templates/admin_dashboard.html`
- **CSS**: `static/css/login.css`, `static/css/admin.css`
- **JS**: `static/js/login.js`, `static/js/admin.js`

### Features
- **Login**: Only admins can log in. Patients are rejected with `403`.
- **Admin Dashboard**:
  - Add, edit, or delete patients in your own organization.
  - The admin is never listed or editable.
  - Update keeps unchanged fields as they are.
- **Logout**: Clears session data from `localStorage` and redirects to `/login`.

### Example Accounts (seeded in `init.sql`)
- Admin (Org 1):
  - Username: `jorge_admin`
  - Password: `jorge123`

- Admin (Org 2):
  - Username: `pepe_admin`
  - Password: `pepe123`

---

## Repository Structure

- `dataset.xlsx` → Input dataset for experimentation
- `backend/` → Docker Compose configuration for PostgreSQL + Go backend
  - `main.go` → Gin backend for admin login and CRUD
  - `init.sql` → Postgres schema and seed data
  - `templates/` → HTML views
  - `static/` → CSS + JS assets
- `LICENSE` → MIT License
- `README.md` → Project description and setup instructions

---

## License

This project is licensed under the MIT License.
