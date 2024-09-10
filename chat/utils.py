# chat/utils.py
import PyPDF2

def pdf_to_text(pdf_file):
    reader = PyPDF2.PdfFileReader(pdf_file)
    text = ""
    for page_num in range(reader.numPages):
        page = reader.getPage(page_num)
        text += page.extractText()
    return text
