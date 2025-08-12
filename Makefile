default: run

summarize:
	python -m summarizer.summarize
clean:
	rm -rf summaries/* reports/*
	rm -rf env/
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf build/ dist/ *.egg-info/
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".DS_Store" -delete

install:
	python3 -m venv env
	. env/bin/activate && pip install -r requirements.txt

run:
	. env/bin/activate && streamlit run ui/streamlit_app.py

.PHONY: default summarize clean install run