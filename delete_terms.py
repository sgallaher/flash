from flask import Flask
from models import db, TblTerms

# Initialize the Flask app
app = Flask(__name__)

# Configure your database URI
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'  # Update with your database URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the app
db.init_app(app)

with app.app_context():
    try:
        # Delete all records in tbl_terms
        db.session.query(TblTerms).delete()
        db.session.commit()
        print("All data in 'tbl_terms' table has been deleted.")
    except Exception as e:
        db.session.rollback()
        print(f"An error occurred: {e}")
