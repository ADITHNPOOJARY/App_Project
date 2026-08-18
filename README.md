# MAD1-project

A Flask-based web application for managing trekking expeditions, staff assignments, and user bookings.

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