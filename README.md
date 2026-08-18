# Trekking Management Web Application

## Overview
This is a full-stack web application designed to manage trekking operations. It provides a seamless interface for managing trekking data, built specifically to showcase backend architecture and API design.

## Tech Stack
* **Backend:** Python, Flask
* **Database:** SQLite (ORM implemented in `models.py`)
* **Frontend:** HTML, CSS (Jinja Templates in `templates/` and `static/`)
* **API:** RESTful API documented with OpenAPI specifications (`api.yaml`)

## Features
* Robust backend database schema using Object-Relational Mapping (ORM) to efficiently store and retrieve user and trekking data.
* Standardized REST API endpoints for scalable client-server communication.
* Clean and responsive frontend interface.

## Prerequisites
Before running the application, ensure you have Python installed on your system. You will also need to install Flask.

1. Open your terminal or command prompt.
2. Install Flask using pip:
   ```bash
   pip install flask
   pip install models
   pip install sqlite3
   pip install datetime

3. Open your terminal and navigate to the project directory (MAD1-PROJECT).

4. If the database is not initialized, run the models file to generate the SQLite database:
    ```bash
    python models.py

5. Start the Flask development server by running:
    ```bash
    python app.py

6. Open your web browser and navigate to:
    ```bash
    http://127.0.0.1:5000/signup

7. To access the Admin Dashboard, open your web browser and navigate to:
   ```bash
   http://127.0.0.1:5000/admin/dashboard


