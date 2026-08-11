# QSR Agentic Analytics

An intelligent, deployment-ready analytics assistant for Quick Service Restaurants (QSRs). This project transforms raw business data into executive-ready insights by combining ETL, SQL analytics, natural-language understanding, and LLM-powered storytelling in one end-to-end experience.

## 🌟 Why this project stands out

- Turns business questions into actionable analytics instantly
- Bridges the gap between raw data and decision-making
- Delivers a modern chat-style experience for non-technical users
- Built for both local demos and real deployment environments

## ✨ Core Features

- ETL pipeline to load Excel sheets into SQLite
- Natural-language question classification
- Pre-built analytics for revenue, store performance, channels, SKUs, cities, weekday/weekend trends, festive vs. normal periods, and declining stores
- AI-generated executive-style insights using an LLM
- FastAPI backend with health and ask endpoints
- Clean chat UI served from a static frontend
- Environment-based configuration for easy deployment

## 🧠 Project Structure

```text
qsr-agentic-analytics/
├── agents/
│   ├── intent_agent.py
│   ├── insight_agent.py
│   └── llm_client.py
├── static/
│   └── index.html
├── etl.py
├── main.py
├── orchestrator.py
├── queries.py
├── test_all.py
├── requirements.txt
├── Procfile
├── .env.example
└── README.md
```

## �️ How it works

1. The ETL layer loads the Excel dataset into SQLite.
2. The intent layer classifies the user's question into a supported analytics category.
3. The query layer runs the correct business analysis.
4. The insight layer converts the results into a polished business narrative.
5. The FastAPI app exposes this experience through a simple web interface.

## �🚀 Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file based on `.env.example` and fill in the required values:

```env
LLM_PROVIDER=groq
GROQ_API_KEY=your_groq_api_key_here
QSR_EXCEL_PATH=./QSR_Agentic_Insights_Dataset.xlsx
QSR_DB_PATH=./qsr.db
HOST=127.0.0.1
PORT=8000
AUTO_PORT=true
```

### 3. Run the app

```bash
python main.py
```

Then open:

```text
http://127.0.0.1:8000
```

## 🧪 Run Tests

```bash
python test_all.py
```

This runs a suite of representative business questions and writes the output to `test_results.txt`.

## 🔗 API Endpoints

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Confirms the service is running |
| `POST /ask` | Accepts a business question and returns analytics + insight |
| `GET /` | Serves the frontend UI |

## 📦 Deployment Ready

The project is structured for deployment with:

- `requirements.txt` for dependencies
- `Procfile` for process startup
- environment-based configuration for secrets and paths

For hosted deployments, provide the real LLM API key and ensure the dataset path is available in the environment.

## 💡 Example Questions

- `GET /health` → health check
- `POST /ask` → send a natural-language question and receive analytics + insight
- `GET /` → serves the frontend UI

## 🧱 Deployment Notes

The app is ready for deployment-friendly hosting with:

- `requirements.txt` for dependencies
- `Procfile` for process startup
- environment variable support for secrets and paths

For production deployments, provide your real LLM API key and make sure the Excel dataset path is available in the host environment.

## 📌 Example Questions

Try asking questions like:

- What were the total revenue, orders, and average order value for the last 3 months?
- Which are the top 5 and bottom 5 stores by revenue?
- Which cities have shown a decline in revenue over the last 3 months?
- Which stores have consistently declined in the last 3 months, and what are the key reasons?

## 🛡️ Security Notes

- Keep your `.env` file local and never commit secrets to GitHub.
- The app automatically bootstraps the SQLite database if needed.
- For production setups, use secure environment variables rather than hard-coded credentials.

## 👨‍💻 Author

Built as an intelligent QSR analytics assistant with FastAPI, SQLite, pandas, and LLM-powered insight generation.
