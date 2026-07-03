import re
# pyrefly: ignore [missing-import]
import nltk

# Attempt to load NLTK resources directly first; download with fast timeout if missing
try:
    # pyrefly: ignore [missing-import]
    from nltk.corpus import stopwords
    # pyrefly: ignore [missing-import]
    from nltk.tokenize import word_tokenize
    STOPWORDS = set(stopwords.words('english'))
    # Validate tokenizer works (implies punkt is loaded)
    word_tokenize("test sentence")
except (ImportError, LookupError):
    import socket
    orig_timeout = socket.getdefaulttimeout()
    try:
        # Set short socket timeout to fail fast if offline
        socket.setdefaulttimeout(3.0)
        nltk.download('punkt', quiet=True)
        nltk.download('stopwords', quiet=True)
        # pyrefly: ignore [missing-import]
        from nltk.corpus import stopwords
        # pyrefly: ignore [missing-import]
        from nltk.tokenize import word_tokenize
        STOPWORDS = set(stopwords.words('english'))
    except Exception:
        # Minimal fallback stopwords list in case of network/permission errors
        STOPWORDS = set([
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours", "yourself",
            "yourselves", "he", "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself",
            "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", "this", "that",
            "these", "those", "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
            "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because",
            "as", "until", "while", "of", "at", "by", "for", "with", "about", "against", "between", "into",
            "through", "during", "before", "after", "above", "below", "to", "from", "up", "down", "in", "out",
            "on", "off", "over", "under", "again", "further", "then", "once", "here", "there", "when", "where",
            "why", "how", "all", "any", "both", "each", "few", "more", "most", "other", "some", "such", "no",
            "nor", "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can", "will", "just",
            "don", "should", "now"
        ])
        def word_tokenize(text):
            return re.findall(r'\b\w+\b', text.lower())
    finally:
        try:
            socket.setdefaulttimeout(orig_timeout)
        except Exception:
            pass

# Define standard headers for resume parsing
SECTION_HEADERS = {
    'experience': [
        'experience', 'work experience', 'professional experience', 'employment history',
        'work history', 'professional background', 'employment', 'career history'
    ],
    'education': [
        'education', 'academic background', 'academic history', 'qualification',
        'qualifications', 'education history', 'degrees', 'academic qualifications'
    ],
    'skills': [
        'skills', 'technical skills', 'core competencies', 'professional skills',
        'technologies', 'languages and technologies', 'key skills', 'areas of expertise'
    ],
    'projects': [
        'projects', 'academic projects', 'personal projects', 'key projects',
        'featured projects', 'technical projects', 'undertakings'
    ],
    'contact': [
        'contact', 'contact info', 'contact details', 'personal information',
        'links', 'social media', 'personal details'
    ]
}

def clean_text(text):
    """
    Cleans raw text by removing URLs, emails, special characters, numbers, and extra spaces.
    """
    if not text:
        return ""
    
    # Lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', ' ', text)
    
    # Remove Emails
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', ' ', text)
    
    # Remove Phone numbers (simple pattern)
    text = re.sub(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', ' ', text)
    
    # Replace newlines and tabs with spaces
    text = re.sub(r'[\r\n\t]+', ' ', text)
    
    # Remove punctuation & special characters (keep letters and basic spaces)
    text = re.sub(r'[^\w\s#+-]', ' ', text)  # Keep # for C# and + for C++
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def preprocess_text(text):
    """
    Cleans text, tokenizes, and removes stopwords.
    Returns a space-separated string of tokens.
    """
    cleaned = clean_text(text)
    try:
        tokens = word_tokenize(cleaned)
    except Exception:
        tokens = re.findall(r'\b\w+\b', cleaned)
        
    filtered_tokens = [t for t in tokens if t not in STOPWORDS and len(t) > 1]
    return " ".join(filtered_tokens)

def extract_contact_info(text):
    """
    Helper to extract email, phone number, and links using regex from raw text.
    """
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    phones = re.findall(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', text)
    urls = re.findall(r'https?://[^\s()<>]+(?:\([\w\d]+\)|([^[:punct:]\s]|/))', text)
    
    return {
        'email': emails[0] if emails else "",
        'phone': phones[0] if phones else "",
        'links': list(set(urls))
    }

def extract_sections(text):
    """
    Splits the resume text into sections: experience, education, skills, projects, contact.
    Works by scanning lines for matching section headers.
    """
    sections = {
        'experience': '',
        'education': '',
        'skills': '',
        'projects': '',
        'contact': ''
    }
    
    lines = text.split('\n')
    current_section = None
    accumulated_text = []
    
    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        
        # Check if this line is a section header
        found_header = False
        lower_line = stripped_line.lower().replace(':', '').strip()
        
        # Exact match or starts-with match for section headers
        for sec_name, keywords in SECTION_HEADERS.items():
            if lower_line in keywords or any(lower_line == kw for kw in keywords):
                if current_section:
                    sections[current_section] += '\n'.join(accumulated_text) + '\n'
                current_section = sec_name
                accumulated_text = []
                found_header = True
                break
        
        if not found_header:
            if current_section:
                accumulated_text.append(stripped_line)
            else:
                # Text before any section header is appended to contact or profile
                sections['contact'] += stripped_line + '\n'
                
    if current_section and accumulated_text:
        sections[current_section] += '\n'.join(accumulated_text) + '\n'
        
    # Standardize empty strings and clean
    for key in sections:
        sections[key] = sections[key].strip()
        
    return sections

if __name__ == "__main__":
    test_text = """
    John Doe
    johndoe@gmail.com
    123-456-7890
    github.com/johndoe

    Education
    BS in Computer Science, Stanford University, 2022

    Work Experience
    Software Engineer, Google
    Worked on search backend and infrastructure.

    Technical Skills
    Python, Javascript, React, SQL, Git
    """
    
    print("Testing clean_text:")
    print(clean_text("Python Developer at Google! (2025). http://google.com"))
    
    print("\nTesting extract_sections:")
    print(extract_sections(test_text))
