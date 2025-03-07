#!/bin/bash
# build.sh - Build script for Render deployment of a Python-Flask app with Tailwind CSS

# Exit immediately if any command fails.
set -e

echo "Starting build process for Render deployment..."

# 1. Install Python dependencies.
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 2. Install Node dependencies.
# If a package.json exists, use it; otherwise, install Tailwind CSS globally.
if [ -f package.json ]; then
  echo "Found package.json. Installing Node dependencies..."
  npm install
  
  # Build using npm script
  echo "Building Tailwind CSS using npm script..."
  npm run build:css
else
  echo "No package.json found. Installing Tailwind CSS globally..."
  npm install -g tailwindcss postcss autoprefixer
  
  # Build directly with Tailwind CLI
  echo "Building Tailwind CSS with CLI..."
  tailwindcss -i ./static/css/tailwind.css -o ./static/css/tailwind.compiled.css --minify
fi

# 3. Optional: Run database migrations if using a migration tool (e.g., Flask-Migrate).
# Uncomment the lines below if applicable.
#
# echo "Running database migrations..."
# flask db upgrade

echo "Build process completed successfully."