# Makefile for running functions-framework locally

# Define variables
TARGET=write_to_firestore
DEBUG=--debug
VENV=~/.console_venv
PYTHONPATH=/Users/suryaduggirala/projects/console_be

# Default command to run functions-framework with specified target and debug options
run:
	@echo "Running functions-framework with target $(TARGET) and debug mode..."
	. $(VENV)/bin/activate && \
	export PYTHONPATH=$(PYTHONPATH):$$PYTHONPATH && \
	functions-framework --target=$(TARGET) $(DEBUG)

setup:
	@echo "Setting up virtual environment and PYTHONPATH..."
	. $(VENV)/bin/activate && \
	export PYTHONPATH=$(PYTHONPATH):$$PYTHONPATH
