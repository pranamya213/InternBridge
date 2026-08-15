# InternBridge

InternBridge is an intelligent internship and early-career recruitment platform that connects students and interns with entrepreneurs, startups, and companies.

## Setup Instructions

1. **Clone the repository** (if not already done).

2. **Create a virtual environment**:
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:
   - Windows: `venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables**:
   Copy `.env.example` to `.env` and adjust the values if necessary.
   ```bash
   cp .env.example .env
   ```

6. **Run the application**:
   ```bash
   python run.py
   ```

7. **Access the application**:
   Open a browser and navigate to `http://localhost:5000`
