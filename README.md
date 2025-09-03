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

## Repository Structure

- `dataset.xlsx` → Input dataset for experimentation
- `backend/` → Docker Compose configuration for PostgreSQL
- `LICENSE` → MIT License
- `README.md` → Project description and setup instructions

---

## License

This project is licensed under the MIT License.
