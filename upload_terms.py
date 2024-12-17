'''import csv
from flask import Flask
from models import db, TblTerms

# Initialize the Flask app
app = Flask(__name__)

# Configure your database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'  # Update with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

# Path to the uploaded CSV file
csv_file_path = "terms.csv"

with app.app_context():
    try:
        # Open the CSV file
        with open(csv_file_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            # Iterate through each row in the CSV
            for row in reader:
                term = TblTerms(
                    name=row['name'],
                    definition=row['definition'] if row['definition'] != 'NaN' else None,
                    session_id=int(row['session_id']),
                )

                # Add the term to the session
                db.session.add(term)

            # Commit all changes
            db.session.commit()
            print("Data uploaded successfully to 'tbl_terms' table.")

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")
'''
