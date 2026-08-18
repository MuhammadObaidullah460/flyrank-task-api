# Task API with Supabase Authentication 🚀

This is a FastAPI-based Task Management API that uses PostgreSQL (via Docker) for data storage and **Supabase** for robust user authentication and JWT verification.

## Features Added in This Update
* **User Authentication:** Sign up and Log in functionality using Supabase.
* **JWT Security:** API endpoints are secured using JSON Web Tokens (JWT).
* **Swagger Padlock:** Easily test protected routes directly from the Swagger UI using the Authorize (Lock 🔒) button.
* **Protected Routes:** All Task CRUD operations are now strictly protected and require a valid Bearer Token.

## Prerequisites
* Docker and Docker Compose
* A Supabase Account (Free Tier)

## Environment Variables (.env)
Before running the application, set up your environment variables. Create a `.env` file in the root directory (you can copy `.env.example` if available) and add your Supabase credentials:

```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_anon_public_key
```
## How to Run
Run the following command in your terminal to start the entire stack (API + Database):
```bash
docker compose up --build
```

## Endpoints

| Method | Path | Meaning |
|---|---|---|
| GET | `/` | API details |
| GET | `/health` | Health check |
| POST | `/auth/signup` | Register a new user |
| POST | `/auth/login` | Login and get JWT |
| GET | `/public/info` | Public info route |
| GET | `/protected/profile`| Get logged-in user profile (Protected 🔒) |
| GET | `/tasks` | List all tasks (Protected 🔒) |
| GET | `/tasks/{id}` | Get a specific task (Protected 🔒) |
| POST | `/tasks` | Create a new task (Protected 🔒) |
| PUT | `/tasks/{id}` | Update a task (Protected 🔒) |
| DELETE | `/tasks/{id}` | Delete a task (Protected 🔒) |

## Example Request 
To test the API, you can use this curl command:
```bash
curl -i http://localhost:8000/public/info
```
