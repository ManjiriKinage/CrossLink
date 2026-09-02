import re
import unicodedata

def clean_text(raw_text: str) -> str:
    """
    Cleans and normalizes raw text for NLP processing.
    - Normalizes Unicode characters
    - Normalizes quotes, apostrophes, and dashes
    - Replaces excessive whitespace and carriage returns
    """
    if not raw_text:
        return ""
    
    # Normalize unicode
    text = unicodedata.normalize("NFKC", raw_text)
    
    # Replace smart quotes and dashes
    text = text.replace('“', '"').replace('”', '"').replace('’', "'").replace('‘', "'")
    text = text.replace('—', ' - ').replace('–', ' - ')
    
    # Normalize carriage returns
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Collapse multiple blank lines into two newlines (paragraphs)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Replace tabs and multiple horizontal spaces with a single space
    lines = []
    for line in text.split('\n'):
        cleaned_line = re.sub(r'[ \t]+', ' ', line).strip()
        lines.append(cleaned_line)
    
    return '\n'.join(lines).strip()
