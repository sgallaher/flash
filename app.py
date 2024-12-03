from io import TextIOWrapper
import csv, re, io
from flask import Flask, request, render_template, redirect, send_file, session, url_for
from flask_bcrypt import Bcrypt
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from models import TblTerms, TblLessons, TblUnits, TblCards, db

app = Flask(__name__)
app.secret_key = 'refhtrrv65eccTdF'  # Set secret key first
bcrypt = Bcrypt(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flashcards.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# Initialize the database
db.init_app(app)

''' -------------Code for the generation of the PDF Cards -----------'''

# Adjusted card dimensions for 4 rows x 2 columns layout
CARD_WIDTH = 90 * mm  # Slightly wider
CARD_HEIGHT = 55 * mm  # Adjusted height for 8 cards per page

# A4 dimensions
A4_WIDTH, A4_HEIGHT = A4

def generate_pdf(cards):

    '''Check if this is being calleld'''

    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)

    # Margins and spacings
    margin_top = 15 * mm
    margin_left = 10 * mm
    gap_between_rows = 5 * mm
    gap_between_columns = 10 * mm

    # Calculate positions for 8 cards (4 rows x 2 columns)
    positions = [
        (margin_left + (col * (CARD_WIDTH + gap_between_columns)),
         A4_HEIGHT - margin_top - (row * (CARD_HEIGHT + gap_between_rows)) - CARD_HEIGHT)
        for row in range(4)
        for col in range(2)
    ]

    # Style for wrapped text
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontSize = 12
    style.leading = 14  # Line spacing
    style.alignment=1
  



    # Split cards into front and back pages
    num_pages = (len(cards) + 7) // 8  # 8 cards per page
    for page in range(num_pages):
        # Front side (terms)
        style.fontSize = 20
        for i in range(8):
            index = page * 8 + i
            if index >= len(cards):
                continue
            term, _ = cards[index]
            x, y = positions[i]
            draw_wrapped_text(c, term, x, y, CARD_WIDTH, style)

        c.showPage()

        # Back side (definitions)
        style.fontSize = 10
        style.alignment=0
        for i in range(8):
            index = page * 8 + i
            if index >= len(cards):
                continue
            _, definition = cards[index]
            # Flip horizontal alignment for back side
            x, y = positions[i]
            x = A4_WIDTH - x - CARD_WIDTH
            draw_wrapped_text(c, definition, x, y, CARD_WIDTH, style)

        c.showPage()

    c.save()
    packet.seek(0)
    return packet

def draw_wrapped_text(c, text, x, y, width, style):
    """Draw vertically and horizontally centered wrapped text using a Paragraph."""
    para = Paragraph(text, style)
    from reportlab.platypus.frames import Frame

    # Create a frame for the text and render it on the canvas
    frame = Frame(x, y, width, CARD_HEIGHT, showBoundary=1)
    frame.addFromList([para], c)

''' -------------- End generation of PDF Card code --------------------'''

    
def validate_input(input_str):
    if re.search(r'(DROP|SELECT|INSERT|DELETE|UPDATE|;|--|#)', input_str, re.IGNORECASE):
        raise ValueError("Potential SQL injection attempt detected")
    return input_str

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
        session["title"]=None
    if "print" not in session:
        session["print"]=None
    
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
            session['title']=str(query.unit.year)+"-"str(query.unit.number)+" "+str(query.lesson.number)
            make_lesson=int(request.form.get('make_lesson'))
            session['print']=make_lesson

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
            #this works

            # Process each line and add to the database
            for line in terms_definitions.splitlines():
                if ':' in line:  # Ensure format is "Term: Definition"
                    term, definition = map(str.strip, line.split(':', 1))
                    print("Split worked")
                    nextId = db.session.query(TblTerms).order_by(TblTerms.term_id.desc()).first()
                    print(f"Next term_id is {nextId.term_id+1}")
                    new_term = TblTerms(term_id=nextId.term_id+1, name=term, definition=definition, session_id=0)
                    db.session.add(new_term)
                    print(f"added {new_term}")

                    nextCardId = db.session.query(TblCards).order_by(TblCards.card_id.desc()).first()
                    print(f"Next card_id is {nextCardId.card_id+1}")
                    new_card = TblCards(card_id=nextCardId.card_id+1, term_id=nextId.term_id+1, lesson_id=session["lesson"], session_id=0)
                    db.session.add(new_card)
            
            # Commit changes to the database
            db.session.commit()

            # Redirect to the same page to display updated terms
            return redirect("/")
        except:
            print("Error")
        

    
    if session['print']:
        # Query the database to get the cards related to this lesson
        query = db.session.query(TblCards).join(TblTerms).join(TblLessons).join(TblUnits).filter(TblLessons.lesson_id == session["print"]).all()
        
        # Create the cards list (extract terms and definitions)
        cards = [(card.term.name, card.term.definition) for card in query]


        # Generate the PDF with the cards data
        pdf = generate_pdf(cards)
        dl=f'flashcardsLesson{session['print']}.pdf'
        session['print']=None

        return send_file(pdf, as_attachment=True, download_name=dl, mimetype='application/pdf')




        

    

    return render_template("/index.html", results=query, lessons=lessons)






