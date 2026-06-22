.PHONY: install run test lint clean dashboard all

install:
	pip install -r requirements.txt

run:
	python run_pipeline.py

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

lint:
	ruff check src/ tests/

dashboard:
	streamlit run app/streamlit_app.py

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete

all: install run test dashboard
