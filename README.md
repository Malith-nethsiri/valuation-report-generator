# Data Collection & DOCX Generation Web App

A modern web application that collects user data and generates downloadable DOCX files.

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PostgreSQL** (Neon.tech) - Database
- **python-docx** - DOCX file generation

### Frontend
- **React** - UI library
- **Vite** - Build tool
- **TypeScript** - Type safety
- **TailwindCSS** - Styling
- **shadcn/ui** - UI components

## Project Structure

```
project/
├── backend/          # Python FastAPI backend
│   ├── app/         # Application code
│   └── requirements.txt
├── frontend/        # React frontend
│   └── src/
├── .gitignore
└── README.md
```

## Setup Instructions

### Backend Setup

1. Navigate to backend directory:
   ```bash
   cd backend
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   ```

3. Activate virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Create `.env` file with database connection string

6. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Navigate to frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run development server:
   ```bash
   npm run dev
   ```

## Features

- User data collection form
- Data validation
- PostgreSQL data persistence
- Dynamic DOCX file generation
- File download functionality
- Modern, responsive UI

## API Endpoints

- `POST /api/submit` - Submit user data
- `POST /api/generate-docx` - Generate and download DOCX file
- `GET /api/health` - Health check

## Development

- Backend runs on: http://localhost:8000
- Frontend runs on: http://localhost:5173
- API documentation: http://localhost:8000/docs

## License

MIT
