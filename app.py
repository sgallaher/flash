from io import TextIOWrapper
import csv, re, os
from flask import Flask, request, render_template, redirect, send_file, session, url_for, flash
from flask_bcrypt import Bcrypt
from datetime import datetime


from models import *
from dotenv import load_dotenv
#from cardsold import *
from cards import *
from itsdangerous import URLSafeTimedSerializer
import smtplib  # Or use a library like Flask-Mail
from authlib.integrations.flask_client import OAuth


app = Flask(__name__)
app.secret_key = 'your_secret_key'
serializer = URLSafeTimedSerializer(app.secret_key)
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



oauth= OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    authorize_url="https://accounts.google.com/o/oauth2/auth",  # Explicitly set this
    client_kwargs={"scope": "openid profile email"}
    
)



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
    if "token" not in session:
        session['token']=None

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
                
                #Generate next print_id
                next = db.session.query(db.func.max(TblPrintedCards.print_id)).scalar()
                printId = (next or 0) + 1


                # Get current timestamp
                timestamp = int(datetime.now().timestamp())

                #write record of print to db
                new_printed = TblPrintedCards(
                    print_id=printId,
                    session_id=session.get('id'),
                    lesson_id=session.get('lesson'),
                    created=timestamp
                )

                # Add to the database
                db.session.add(new_printed)
                db.session.commit()

                session['print']=None

                return send_file(pdf, as_attachment=True, download_name=dl, mimetype='application/pdf')
        except:
            pass

        try:
            term_id = request.form.get('term_id')
            term_name = request.form.get('term_name')
            term_definition = request.form.get('term_definition')
            print(term_name,term_definition)
            if term_id and term_name and term_definition:
                print(term_id)
                # Fetch the term from the database
                term = TblTerms.query.get(term_id)
                if term:
                    # Update the term with the new data
                    term.name = term_name
                    term.definition = term_definition
                    term.session_id=session.get('id'),
                    db.session.commit()
                    return redirect('/')
            
                else:
                    print("Term not found.", "error")
            else:
                
                print("All fields are required.", "error")
        except:
            pass

        


        ''' -------------------- check if any new terms have been posted, and if so, add them to database ------------''' 
        try:
            terms_definitions = request.form.get('terms_definitions', '').strip()
            

            # Process each line and add to the database
            for line in terms_definitions.splitlines():
                if ':' in line:  # Ensure format is "Term: Definition"
                    term, definition = map(str.strip, line.split(':', 1))
                    print("Split worked")
                    nextId = db.session.query(TblTerms).order_by(TblTerms.term_id.desc()).first()
                    print(f"Next term_id is {nextId.term_id+1}")
                    new_term = TblTerms(term_id=nextId.term_id+1, name=term, definition=definition, session_id=session.get('id'))
                    db.session.add(new_term)
                    print(f"added {new_term}")

                    nextCardId = db.session.query(TblCards).order_by(TblCards.card_id.desc()).first()
                    print(f"Next card_id is {nextCardId.card_id+1}")
                    new_card = TblCards(card_id=nextCardId.card_id+1, term_id=nextId.term_id+1, lesson_id=session["lesson"], session_id=session.get('session'))
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
    allsessions=db.session.query(TblSessions).join(TblUsers).all()
    titles = TblTitles.query.all()
    roles = TblRoles.query.all()
    units = TblUnits.query.all()
    lessons = TblLessons.query.all()
    allprints = TblPrintedCards.query.all()
    return render_template("/viewdb/index.html", allusers=allusers, titles=titles, units=units, lessons=lessons,allsessions=allsessions, allprints=allprints)


@app.route("/login", methods=['POST', 'GET'])
def login():
    
    message = "Sign In"
    if "user" not in session:
        session["user"] = None
    if 'role_id' not in session:
        session['role_id'] = None
    if 'id' not in session:
        session['id'] = None

    if "attempts" not in session:
        session["attempts"] = 0
    #for testing purpose, set the attempts to 0, no matter what!
    session['attempts']=0

    if request.method == 'POST':
        # Get the email and plain text password
        username = request.form.get('user')
        pw = request.form.get('password')

        # Query database to find the user
        user = db.session.query(TblUsers.email, TblUsers.password, TblUsers.role_id).filter(TblUsers.email == username).first()

        if user and session['attempts'] < 3:
            # Check the password using Flask-Bcrypt
            if check_password(pw, user.password):
                session['user'] = username
                session['role_id']=user.role_id
                session['attempts'] = 0
                #get the last session id and add one.
                # Generate new session_id
                last_session = db.session.query(db.func.max(TblSessions.session_id)).scalar()
                new_session_id = (last_session or 0) + 1
                session['id'] = new_session_id

                # Get current timestamp
                timestamp = int(datetime.now().timestamp())

                # Create new session entry
                new_session = TblSessions(
                    session_id=new_session_id,
                    user_id=user.user_id,
                    created=timestamp,
                    duration=360,  # Default duration
                    terminated=None
                )

                # Add to the database
                db.session.add(new_session)
                db.session.commit()
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
        print(hashed_password)

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
        print(new_user)

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


@app.route('/login/google')
def login_google():
    try:
        redirect_uri=url_for('authorize_google', _external=True)
        #developmental url
        #return google.authorize_redirect(redirect_uri=f"https://{CODESPACE_NAME}-5000.app.github.dev/authorize/google")
        #deployed url
        return google.authorize_redirect(redirect_uri=f"https://mysterious-sherill-shanegallaher-435e1a89.koyeb.app/authorize/google")
        
    except Exception as e :
        app.logger.error(f"Error during login:{str(e)}")
        return "Error occurred during login", 500
    

@app.route('/authorize/google')
def authorize_google():
    token= google.authorize_access_token()
    userinfo_endpoint=google.server_metadata['userinfo_endpoint']
    resp = google.get(userinfo_endpoint)
    user_info = resp.json()
    username=user_info['email']
    temp=username.split("@")
    profile_picture = user_info.get('picture')

    user=TblUsers.query.filter_by(email=username).first()
    if not user:
            
            new_user = TblUsers(
                user_id=temp[0],
                first_name=temp[0][0],
                last_name=temp[0][1:],
                title_id="", #no idea of gender
                email=username,
                #not storing password and security questions

                role_id=1,#create all users as normal from now on. Need to contact to make admin
                created=int(datetime.utcnow().timestamp())
            )
            db.session.add(new_user)
            db.session.commit()
    session['user']= temp[0]
    session["oauth_token"] = token
    session['role_id']=user.role_id
    session['profile_picture'] = profile_picture  # Save profile picture in the session
     #get the last session id and add one.
    # Generate new session_id
    last_session = db.session.query(db.func.max(TblSessions.session_id)).scalar()
    new_session_id = (last_session or 0) + 1
    session['id'] = new_session_id

    # Get current timestamp
    timestamp = int(datetime.now().timestamp())

    # Create new session entry
    new_session = TblSessions(
        session_id=new_session_id,
        user_id=user.user_id,
        created=timestamp,
        duration=360,  # Default duration
        terminated=None
    )

    # Add to the database
    db.session.add(new_session)
    db.session.commit()

    return redirect(url_for('index'))
        


# Route to edit lessons
@app.route('/editlessons', methods=['GET', 'POST'])
def edit_lessons():

    """Export tbl_lessons table to a CSV file."""
    output_file = "tbl_lessons_export.csv"  # Name of the CSV file

    # Query all rows in the table
    lessons = TblLessons.query.all()

    # Open CSV file for writing
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        # Write the header row
        writer.writerow(['lesson_id', 'unit_id', 'number', 'name', 'session_id'])  # Update as per your table columns
        '''
        lesson_id = db.Column(db.Integer, primary_key=True)
            unit_id = db.Column(db.String(10), db.ForeignKey('tbl_units.unit_id'), nullable=False)
            number = db.Column(db.Integer, nullable=False)
            name = db.Column(db.String(64), nullable=True)
            session_id = db.Column(db.Integer, db.ForeignKey('tbl_sessions.session_id'), nullable=False)

            session = db.relationship('TblSessions', backref='lessons')
            unit = db.relationship('TblUnits', backref='lessons')

        '''
        # Write data rows
        for lesson in lessons:
            writer.writerow([
                lesson.lesson_id,  # Adjust column names based on your TblLessons model
                lesson.unit_id,
                lesson.number,
                lesson.name,
                lesson.session_id
            ])

    print(f"Data successfully exported to {output_file}.")
    return redirect(url_for('viewdb'))

