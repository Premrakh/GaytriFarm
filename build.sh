#!/bin/bash

# Check if Poetry is installed, if not install it
if ! command -v poetry &> /dev/null
then
    echo "Poetry not found, installing..."
    pip install poetry==1.7.1
fi

# Configure Poetry to not create virtual environments
poetry config virtualenvs.create false

# Install dependencies
echo "Installing dependencies..."
poetry install --no-dev

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build completed successfully!"
