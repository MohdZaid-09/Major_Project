from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUTPUT = "project_progress_comparison.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="TitleCustom", parent=styles["Title"], fontName="Helvetica-Bold",
    fontSize=22, leading=27, alignment=TA_CENTER, textColor=colors.HexColor("#176b54"),
    spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="Subtitle", parent=styles["Normal"], fontName="Helvetica",
    fontSize=10, leading=14, alignment=TA_CENTER, textColor=colors.HexColor("#687582"),
    spaceAfter=18,
))
styles.add(ParagraphStyle(
    name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold",
    fontSize=14, leading=18, textColor=colors.HexColor("#0d4d3c"), spaceBefore=14, spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="BodyCustom", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=9.5, leading=14, textColor=colors.HexColor("#202a35"), spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="Cell", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=8.2, leading=11, textColor=colors.HexColor("#202a35"),
))
styles.add(ParagraphStyle(
    name="CellBold", parent=styles["BodyText"], fontName="Helvetica-Bold",
    fontSize=8.2, leading=11, textColor=colors.HexColor("#202a35"),
))
styles.add(ParagraphStyle(
    name="Small", parent=styles["BodyText"], fontName="Helvetica",
    fontSize=8.5, leading=12, textColor=colors.HexColor("#687582"),
))


def p(text, style="Cell"):
    return Paragraph(text, styles[style])


doc = SimpleDocTemplate(
    OUTPUT, pagesize=A4, rightMargin=15 * mm, leftMargin=15 * mm,
    topMargin=14 * mm, bottomMargin=14 * mm,
)

story = [
    p("SwasthAI Project Progress", "TitleCustom"),
    p("Comparison with the previous version | 12 September 2026", "Subtitle"),
    p("This report summarizes the implemented improvements toward the final multilingual healthcare assistant goal.", "BodyCustom"),
    p("Progress Comparison", "Section"),
]

rows = [
    [p("Area", "CellBold"), p("Previous version", "CellBold"), p("Current version", "CellBold")],
    [p("Medical perspectives", "CellBold"), p("Allopathic, Ayurvedic, and Homeopathic views", "Cell"), p("Added Unani as the fourth visible perspective", "Cell")],
    [p("Knowledge base", "CellBold"), p("Local Chroma retrieval was available", "Cell"), p("Retrieves four focused chunks from the latest question for faster context", "Cell")],
    [p("Conversation history", "CellBold"), p("History was flattened into the prompt", "Cell"), p("Structured history is sent separately to the backend", "Cell")],
    [p("Chat persistence", "CellBold"), p("Messages disappeared after refresh", "Cell"), p("Messages persist in browser localStorage", "Cell")],
    [p("Voice conversation", "CellBold"), p("Used plain text context", "Cell"), p("Uses the same structured history format as typed chat", "Cell")],
    [p("Response parsing", "CellBold"), p("Missing fields could cause failures", "Cell"), p("Missing remedy fields receive safe defaults", "Cell")],
    [p("API reliability", "CellBold"), p("The chat route could return null due to an indentation bug", "Cell"), p("Successful chat responses now return correctly", "Cell")],
    [p("Frontend caching", "CellBold"), p("Older UI could remain visible", "Cell"), p("Added cache busting and no-cache homepage headers", "Cell")],
    [p("Source display", "CellBold"), p("No structured source panel", "Cell"), p("Source panel was tested, then removed from the visible UI as requested; RAG remains active internally", "Cell")],
    [p("Validation", "CellBold"), p("Node.js was unavailable", "Cell"), p("Node.js installed; JavaScript syntax and Python source checks pass", "Cell")],
]

table = Table(rows, colWidths=[35 * mm, 67 * mm, 67 * mm], repeatRows=1)
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#176b54")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#dce2e7")),
    ("BACKGROUND", (0, 1), (-1, -1), colors.white),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7f6")]),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(table)

story.extend([
    p("Current Architecture", "Section"),
    p("The application currently includes a browser frontend with text and voice input, a FastAPI backend, Chroma vector retrieval, multilingual embeddings, structured conversation history, LLM provider routing through Anthropic, Gemini, or Ollama, four medical perspectives, text-to-speech support, and persistent browser chat history.", "BodyCustom"),
    p("Remaining Gaps", "Section"),
    p("1. GPT-3.5 is not currently the required provider.\n2. Appointment and reminder functionality is not implemented.\n3. There is no dedicated translation module.\n4. There is no backend database for multi-user conversation storage.\n5. There is no dedicated NLP preprocessing module.\n6. Emergency triage and medical safety validation can be expanded.\n7. The latest server start attempt exited with code 1 and still needs diagnosis.", "BodyCustom"),
    p("Validation Status", "Section"),
    p("Frontend JavaScript syntax validation passed with Node.js. Python AST validation passed for the updated API and services. Structured history filtering was also tested successfully. A regular Python bytecode compile was once blocked by a locked Windows __pycache__ file, so the no-write AST check was used instead.", "BodyCustom"),
    Spacer(1, 8),
    p("Prepared for the SwasthAI project review", "Small"),
])

doc.build(story)
print(OUTPUT)
