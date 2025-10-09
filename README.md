# Telegram Spaced Repetition Mini App

A Telegram Mini App for learning new words using spaced repetition with the FSRS (Free Spaced Repetition Scheduler) algorithm.

## Project Structure

```
├── app/
│   └── main.py                # FastAPI application
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## Installation

### Local Development

#### Backend Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd quran-web-app
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

## License

MIT License - see LICENSE file for details.
