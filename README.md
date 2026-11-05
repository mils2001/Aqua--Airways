# ✈️ Aqua Airways

**Beyond Every Destination.**

Aqua Airways is a flight booking and airline management web application designed to make discovering flights and managing reservations easier. Users can explore destinations, search available flights, create accounts, book flights and manage their reservations.

## 📌 Project Overview

Aqua Airways provides a platform where passengers can search for available flights, view journey information and manage their bookings through a simple and responsive interface.

The project uses a React frontend and a Flask backend, with a database for storing application information.

## ✨ Features

### Passenger Features
- User registration and login.
- Secure authentication using JWT.
- Browse available flight routes.
- Search flights by departure city, destination and date.
- View flight schedules and available seats.
- Select flights and create bookings.
- Receive booking confirmation and reference numbers.
- View personal bookings.
- Cancel eligible bookings.
- View and manage passenger profiles.

### General Features
- Responsive user interface.
- Destination images and promotional sections.
- Flight information and pricing.
- Navigation between application pages.

## 🛠️ Technologies Used

### Frontend
- React
- TypeScript
- Vite
- React Router
- Lucide React
- CSS

### Backend
- Python
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-JWT-Extended
- Flask-Bcrypt
- Flask-CORS

### Database
- SQLite

### Development Tools
- Git
- GitHub
- Visual Studio Code
- Linux

## 📂 Project Structure

```text
Aqua-Airways/
│
├── backend/
│   ├── app/
│   │   ├── models/
│   │   ├── routes/
│   │   ├── controllers/
│   │   ├── schemas/
│   │   └── __init__.py
│   │
│   ├── migrations/
│   ├── instance/
│   ├── config.py
│   ├── seed.py
│   └── requirements.txt
│
├── frontend/
│   ├── public/
│   │   └── images/
│   │       └── destinations/
│   │
│   ├── src/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── App.tsx
│   │   ├── App.css
│   │   └── main.tsx
│   │
│   ├── package.json
│   └── index.html
│
└── README.md
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/mils2001/Aqua-Airways.git
```

Navigate into the project:

```bash
cd Aqua-Airways
```

### 2. Backend Setup

Navigate to the backend:

```bash
cd backend
```

Create a virtual environment:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Initialize or update the database migrations if required:

```bash
flask db upgrade
```

Seed the database:

```bash
python seed.py
```

Start the Flask server:

```bash
flask run --host=127.0.0.1 --port=5000
```

The backend will be available at:

`http://127.0.0.1:5000`

### 3. Frontend Setup

Open another terminal and navigate to the frontend:

```bash
cd Aqua-Airways/frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will normally be available at:

`http://localhost:5173`

## 🔌 API Endpoints

The backend exposes REST API endpoints for application functionality.

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/register` | Register a passenger |
| POST | `/api/auth/login` | Log in a passenger |
| GET | `/api/auth/profile` | Get authenticated user profile |
| GET | `/api/flights` | Retrieve available flights |
| GET | `/api/bookings` | Retrieve passenger bookings |
| POST | `/api/bookings` | Create a booking |
| PATCH | `/api/bookings/:id/cancel` | Cancel a booking |
| GET | `/api/schedules/:id` | Retrieve a flight schedule |

Protected endpoints require a valid JWT access token.

## 🧪 Testing

Build the frontend to check for TypeScript and production build errors:

```bash
npm run build
```

Test the backend health endpoint, if enabled:

```bash
curl http://127.0.0.1:5000/api/health
```

You can also test API endpoints using curl or Postman.

## 🔐 Environment Configuration

Keep secret keys and environment-specific settings in environment variables.

Do not commit:
- Database files containing private information.
- JWT secret keys.
- Passwords.
- Private environment configuration files.

Use an example environment file to document the required variables without exposing real secrets.

## 🚀 Future Improvements

Planned improvements may include:

- Online payment integration.
- Electronic ticket generation.
- Email booking notifications.
- Passenger check-in.
- Flight status notifications.
- Airline administration dashboard.
- Passenger loyalty and rewards programme.
- More advanced flight management tools.

## 👨‍💻 Developer

**Christian David**

Software Development

- GitHub: [@mils2001](https://github.com/mils2001)

## 📄 License

This project is developed for educational and portfolio purposes.

---

**Aqua Airways — Beyond Every Destination.**
