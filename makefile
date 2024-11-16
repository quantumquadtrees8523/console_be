# Makefile for running functions-framework locally

# Define variables
TARGET=write_to_firestore
DEBUG=--debug

# Default command to run functions-framework with specified target and debug options
run:
	@echo "Running functions-framework with target $(TARGET) and debug mode..."
	functions-framework --target=$(TARGET) $(DEBUG)
