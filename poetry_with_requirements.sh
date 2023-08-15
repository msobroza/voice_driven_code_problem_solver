#!/bin/bash

# Run the desired poetry command (e.g., add, remove, update)
poetry "$@"

# Export the dependencies to requirements.txt
poetry export -f requirements.txt --output requirements.txt --without-hashes