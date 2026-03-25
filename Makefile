.PHONY: install run dev clean setup ollama-pull kill

# Install dependencies
install:
	pip install -r requirements.txt

# Run production server
run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000

# Run development server with reload
dev:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Kill all Python/uvicorn processes
kill:
	@echo "🔪 Killing Python processes..."
	pkill -f "uvicorn" || true
	pkill -f "python.*app.main" || true
	@echo "✅ Done!"

# Setup environment
setup:
	cp .env.example .env
	mkdir -p fs/plaintables fs/vector_stores uploads
	@echo "✅ Environment setup complete!"

# Pull Ollama model
ollama-pull:
	ollama pull qwen2.5:1.5b

# Clean generated files
clean:
	rm -rf fs/plaintables/* fs/vector_stores/* uploads/*
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned!"

# Full setup
init: setup install ollama-pull
	@echo "🚀 Ready to go! Run 'make dev' to start."
