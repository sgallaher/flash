from io import TextIOWrapper
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
import io

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
