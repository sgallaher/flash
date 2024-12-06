from io import TextIOWrapper
import csv, re
from flask import Flask, request, render_template, redirect, send_file, session, url_for, flash
from flask_bcrypt import Bcrypt
from datetime import datetime

from models import TblTerms, TblLessons, TblUnits, TblCards, TblUsers,TblTitles, TblRoles,db
from cards import *
import cards
from itsdangerous import URLSafeTimedSerializer



app = Flask(__name__)
app.secret_key = 'your_secret_key'
serializer = URLSafeTimedSerializer(app.secret_key)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Initialize the database
db.init_app(app)


    
def validate_input(input_str):
    if re.search(r'(DROP|SELECT|INSERT|DELETE|UPDATE|;|--|#)', input_str, re.IGNORECASE):
        raise ValueError("Potential SQL injection attempt detected")
    return input_str



def hash_password(plaintext_password):
    return bcrypt.generate_password_hash(plaintext_password).decode('utf-8')

# Function to check a password against a hash
def check_password(plaintext_password, hashed_password):
    return bcrypt.check_password_hash(hashed_password, plaintext_password)


'''build the database if it is isn't there yet.'''
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Ensures tables are created
    app.run(debug=True)




''' ---------------------------The "main" -------------------------'''

@app.route('/', methods=["POST","GET"])
def index():

    '''----- check the session variables.  If they aren't there, make them ------'''
    if "lesson" not in session:
        session["lesson"]=None
        
    if "print" not in session:
        session["print"]=None
    if "title" not in session:
        session["title"]=None

    titles = db.session.query(TblLessons, TblUnits).join(TblUnits).filter(TblLessons.lesson_id == session["lesson"]).first()
    if titles:
            lesson, unit = titles
            session['title']= f"{unit.year}.{unit.number} Lesson {lesson.number}"
    
    ''' -----load the cards from db ----------'''


    query = db.session.query(TblCards).join(TblTerms).join(TblLessons).join(TblUnits).filter(TblLessons.lesson_id == session["lesson"]).all()

    ''' -----load the years / units / lessons  from db ----------'''
    lessons = db.session.query(TblLessons).join(TblUnits).order_by(TblLessons.unit_id, TblLessons.number).all()   
    
    '''----- check for a get  for the purpose of deleting a card and term if user hits the trash can ------'''    
    if request.method =="GET":
        try:
            term_id = request.args.get('term') 
            card_id = request.args.get('card') 
            # Query the TblCards table to find the card to delete
            if card_id is None:
                pass
            else:
                card = TblCards.query.get(card_id)
            if term_id is None:
                pass
            else:
                term = TblTerms.query.get(term_id)

            if card:
                db.session.delete(card)  # Delete the row
                db.session.commit()  # Commit the changes

            if term:
                db.session.delete(term)  # Delete the row
                db.session.commit()  # Commit the changes

            return redirect("/")
        except:
            pass


    

    
    '''----- check if the session variables have changed in a post ------'''
    if request.method == 'POST':

        
        '''----- check if the session variables have changed in a post ------'''
        #set lesson to the lesson session
        try:
            session['lesson']=int(request.form.get('lesson_id'))
        except:
            pass
        try:
            make_lesson=request.form.get('make_lesson')
            if make_lesson:

                session['print']=session["lesson"]
                # Query the database to get the cards related to this lesson
                query = db.session.query(TblCards).join(TblTerms).join(TblLessons).join(TblUnits).filter(TblLessons.lesson_id == session["print"]).all()
                
                # Create the cards list (extract terms and definitions)
                cards = [(card.term.name, card.term.definition) for card in query]


                # Generate the PDF with the cards data
                pdf = generate_pdf(cards)
                dl=f'flashcards-{session['title']}.pdf'
                session['print']=None

                return send_file(pdf, as_attachment=True, download_name=dl, mimetype='application/pdf')
        except:
            pass

        try:
            term_id = request.form.get('term_id')
            term_name = request.form.get('term_name')
            term_definition = request.form.get('term_definition')
            
            if term_id and term_name and term_definition:
                
                # Fetch the term from the database
                term = TblTerms.query.get(term_id)
                if term:
                    # Update the term with the new data
                    term.name = term_name
                    term.definition = term_definition
                    db.session.commit()
                    return redirect('/')
            
                else:
                    pass
            else:
                
                print("All fields are required.", "error")
        except:
            pass

        


        ''' -------------------- check if any new terms have been posted, and if so, add them to database ------------''' 
        try:
            terms_definitions = request.form.get('terms_definitions', '').strip()
            #this works

            # Process each line and add to the database
            for line in terms_definitions.splitlines():
                if ':' in line:  # Ensure format is "Term: Definition"
                    term, definition = map(str.strip, line.split(':', 1))
                    
                    nextId = db.session.query(TblTerms).order_by(TblTerms.term_id.desc()).first()
                
                    new_term = TblTerms(term_id=nextId.term_id+1, name=term, definition=definition, session_id=0)
                    db.session.add(new_term)
                   

                    nextCardId = db.session.query(TblCards).order_by(TblCards.card_id.desc()).first()
                    
                    new_card = TblCards(card_id=nextCardId.card_id+1, term_id=nextId.term_id+1, lesson_id=session["lesson"], session_id=0)
                    db.session.add(new_card)
            
            # Commit changes to the database
            db.session.commit()

            # Redirect to the same page to display updated terms
            return redirect("/")
        except:
            print("Error")
        

    

    return render_template("/index.html", results=query, lessons=lessons)

@app.route("/viewdb")
def viewdb():
    allusers = db.session.query(TblUsers.email,TblUsers.role_id).join(TblRoles).all()
    titles = TblTitles.query.all()
    roles = TblRoles.query.all()
    units = TblUnits.query.all()
    lessons = TblLessons.query.all()
    return render_template("/viewdb/index.html", allusers=allusers, titles=titles, units=units, lessons=lessons)


@app.route("/login", methods=['POST', 'GET'])
def login():
    
    message = "Sign In"
    if "user" not in session:
        session["user"] = None
    if "attempts" not in session:
        session["attempts"] = 0


    if request.method == 'POST':
        # Get the email and plain text password
        username = request.form.get('user')
        pw = request.form.get('password')

        # Query database to find the user
        user = db.session.query(TblUsers.email, TblUsers.password).filter(TblUsers.email == username).first()

        if user and session['attempts'] < 3:
            # Check the password using Flask-Bcrypt
            if check_password(pw, user.password):
                session['user'] = username
                session['attempts'] = 0
                return redirect("/")
            else:
                session['attempts'] += 1
                message = "Email or Password is incorrect. Please try again."
        else:
            if session['attempts'] >= 3:
                message = "Too many failed attempts. Please try again later."
    
    return render_template("login/index.html", message=message)



@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Retrieve form data
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        title = request.form.get('title')
        email = request.form.get('email')
        password = request.form.get('password')
        question = request.form.get('question')
        answer = request.form.get('answer')
        role_id = request.form.get('role_id')

        # Generate user_id based on the email prefix
        user_id = email.split('@')[0]

        # Validate that all required fields are filled
        if not all([first_name, last_name, email, password, role_id]):
            message = "All fields are required."
            return render_template('register.html', message=message)

        # Check if the email is already registered
        existing_user = TblUsers.query.filter_by(email=email).first()
        if existing_user:
            message = "Email is already registered. Please log in or use a different email."
            return render_template('register/index.html', message=message)

        # Hash the password
        hashed_password = hash_password(password)
        hashed_answer = hash_password(answer)
        

        # Create the new user
        new_user = TblUsers(
            user_id=user_id,
            first_name=first_name,
            last_name=last_name,
            title_id=title,
            email=email,
            password=hashed_password,
            question=question,
            answer=hashed_answer,
            role_id=int(role_id),
            created=int(datetime.utcnow().timestamp())
        )
        

        # Save the user to the database
        db.session.add(new_user)
        db.session.commit()

        # Redirect to the login page or show success message
        message = "Account created successfully! You can now log in."
        return redirect('/')

    # Render the registration form
    titles = TblTitles.query.all()
    roles = TblRoles.query.all()
    return render_template('register/index.html', titles=titles, roles=roles)
    

@app.route("/logout", )
def logout():
    session.clear()
    return redirect("/")


