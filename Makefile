dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
production:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2