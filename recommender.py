import re
from nlp_utils import extract_sections, extract_contact_info
from matcher import match_resume_with_jd

# Mapping of weak passive resume phrases to strong active alternatives
WEAK_VERB_MAP = {
    r'\bresponsible for\b': 'engineered, spearheaded, or directed',
    r'\bhelped with\b': 'collaborated to design and implement',
    r'\bworked on\b': 'architected, designed, and executed',
    r'\bassisted in\b': 'facilitated and partnered in the execution of',
    r'\bhandled\b': 'orchestrated, managed, or resolved',
    r'\bmade\b': 'created, formulated, or designed',
    r'\bdid\b': 'executed, engineered, or deployed',
    r'\bmanaged\b': 'directed, spearheaded, or steered',
    r'\bled\b': 'spearheaded, guided, or steered',
    r'\bimproved\b': 'optimized, enhanced, or boosted',
    r'\bchanged\b': 'transformed, modernized, or refactored',
    r'\btalked to\b': 'negotiated with, liaised with, or collaborated with'
}

# Metric templates to recommend results-oriented impact
METRIC_RECOMMENDATIONS = [
    "Quantify impact: add a metric (e.g. 'boosted performance by 20%', 'reduced loading time by 15%')",
    "Mention tools: specify the technologies used (e.g. 'using Python and Docker')",
    "Describe the 'why': explain the business value (e.g. 'to streamline operations for 500+ daily users')"
]

def calculate_section_completeness(sections):
    """
    Checks the completeness of standard resume sections.
    Weights:
        experience: 30
        education: 20
        skills: 25
        projects: 15
        contact: 10
    Returns:
        score (0-100), and a list of feedback details.
    """
    feedback = []
    score = 0
    
    # 1. Experience (30 points)
    exp_len = len(sections.get('experience', '').strip())
    if exp_len > 200:
        score += 30
    elif exp_len > 50:
        score += 15
        feedback.append("Your 'Experience' section is brief. Try adding more bullet points details on your duties and achievements.")
    else:
        feedback.append("Critical: Your resume is missing or has a very short 'Experience' section. Recruiters prioritize work history.")
        
    # 2. Education (20 points)
    edu_len = len(sections.get('education', '').strip())
    if edu_len > 50:
        score += 20
    elif edu_len > 10:
        score += 10
        feedback.append("Your 'Education' section is very brief. Ensure you list university, degree, graduation year, and GPA (optional).")
    else:
        feedback.append("Warning: 'Education' section is missing. Please list your academic background.")
        
    # 3. Skills (25 points)
    skills_len = len(sections.get('skills', '').strip())
    if skills_len > 30:
        score += 25
    elif skills_len > 10:
        score += 12
        feedback.append("Your 'Skills' list is small. Add technical proficiencies, frameworks, tools, and databases relevant to your target role.")
    else:
        feedback.append("Warning: 'Skills' section not detected. A dedicated skills section helps parsing systems index your profile.")
        
    # 4. Projects (15 points)
    proj_len = len(sections.get('projects', '').strip())
    if proj_len > 100:
        score += 15
    elif proj_len > 30:
        score += 8
        feedback.append("Your 'Projects' section could be expanded. Adding personal or academic projects demonstrates practical capability.")
    else:
        feedback.append("Tip: No 'Projects' section detected. Add 2-3 technical projects to showcase hands-on application of your skills.")
        
    # 5. Contact (10 points)
    contact_text = sections.get('contact', '')
    contact_info = extract_contact_info(contact_text)
    contact_score = 0
    if contact_info['email']:
        contact_score += 4
    else:
        feedback.append("Critical: No contact email address detected. Ensure your email is clear.")
    if contact_info['phone']:
        contact_score += 4
    else:
        feedback.append("Warning: No phone number detected. Recruiters need a way to call you.")
    if contact_info['links']:
        contact_score += 2
    else:
        feedback.append("Tip: Consider adding professional profile links such as LinkedIn or GitHub.")
        
    score += contact_score
    return score, feedback

def rewrite_sentence(sentence):
    """
    Checks if a sentence contains weak action verbs and proposes a rewritten version.
    """
    sentence_lower = sentence.lower()
    rewritten = sentence
    suggestions = []
    has_weak_verb = False
    
    for pattern, strong_alt in WEAK_VERB_MAP.items():
        if re.search(pattern, sentence_lower):
            # Propose replacement
            has_weak_verb = True
            # Build rewrite replacement suggestions
            match = re.search(pattern, sentence_lower)
            matched_phrase = match.group(0)
            
            # Formulate replacement options
            if "responsible for" in matched_phrase:
                rewritten = re.sub(pattern, "Spearheaded the development of", rewritten, flags=re.IGNORECASE)
            elif "helped with" in matched_phrase:
                rewritten = re.sub(pattern, "Collaborated to design and deploy", rewritten, flags=re.IGNORECASE)
            elif "worked on" in matched_phrase:
                rewritten = re.sub(pattern, "Engineered and optimized", rewritten, flags=re.IGNORECASE)
            elif "managed" in matched_phrase:
                rewritten = re.sub(pattern, "Orchestrated and directed", rewritten, flags=re.IGNORECASE)
            elif "improved" in matched_phrase:
                rewritten = re.sub(pattern, "Optimized and accelerated", rewritten, flags=re.IGNORECASE)
            else:
                # Fallback replacement
                first_alt = strong_alt.split(",")[0]
                rewritten = re.sub(pattern, first_alt, rewritten, flags=re.IGNORECASE)
                
            suggestions.append(f"Replace '{matched_phrase}' with a strong active verb like '{strong_alt}'.")
            
    # If it is a description/bullet point, suggest adding metric values
    if len(sentence.strip()) > 15 and not any(char.isdigit() for char in sentence):
        suggestions.append("Add quantifiable metrics (percentages, hour savings, user scale).")
        
    return {
        'original': sentence.strip(),
        'rewritten': rewritten.strip(),
        'suggestions': suggestions,
        'modified': has_weak_verb or (len(sentence.strip()) > 15 and not any(char.isdigit() for char in sentence))
    }

def analyze_and_rewrite_resume(resume_text):
    """
    Splits experience and projects into bullet points/sentences,
    analyzes each, and provides rewrites.
    """
    sections = extract_sections(resume_text)
    target_text = sections.get('experience', '') + "\n" + sections.get('projects', '')
    
    # Split text into lines (sentences or bullet points)
    lines = target_text.split('\n')
    rewrites = []
    
    for line in lines:
        line = line.strip()
        # Clean bullet indicators
        cleaned_line = re.sub(r'^[\s\-\*\•\d\.\)]+', '', line).strip()
        if len(cleaned_line) < 10:
            continue
            
        analysis = rewrite_sentence(cleaned_line)
        if analysis['modified']:
            rewrites.append(analysis)
            
    return rewrites

def generate_recommendations(match_data, section_score, section_feedback):
    """
    Creates an aggregated improvement checklist for the candidate.
    """
    recommendations = []
    
    # 1. Missing skills suggestions
    missing = match_data.get('missing_skills', [])
    if missing:
        recommendations.append({
            'category': 'Skills Alignment',
            'severity': 'high',
            'message': f"Add missing target skills to your resume: {', '.join(missing[:5])}."
        })
        
    # 2. Score alignment suggestions
    text_sim = match_data.get('text_similarity', 0.0)
    if text_sim < 0.35:
        recommendations.append({
            'category': 'Job Description Relevance',
            'severity': 'medium',
            'message': "Your general resume terminology does not closely match the job description. Customize your professional summary and project descriptions to mirror vocabulary from the job post."
        })
        
    # 3. Section scores suggestions
    for feedback in section_feedback:
        severity = 'medium'
        if 'Critical' in feedback:
            severity = 'high'
        elif 'Tip' in feedback:
            severity = 'low'
            
        recommendations.append({
            'category': 'Structure & Sections',
            'severity': severity,
            'message': feedback
        })
        
    return recommendations

def compute_ats_score(match_data, section_score):
    """
    ATS Score calculation (0-100):
        40% Cosine Text Similarity
        40% Skill match percentage
        20% Section completeness score
    """
    text_sim = match_data.get('text_similarity', 0.0) * 100
    skill_score = match_data.get('skill_score', 0.0) * 100
    
    # Final weighted ATS score
    ats_score = (text_sim * 0.40) + (skill_score * 0.40) + (section_score * 0.20)
    
    # Cap score boundaries
    ats_score = min(max(ats_score, 0), 100)
    return round(ats_score, 1)

def analyze_resume_full(resume_text, jd_text):
    """
    Full pipeline to run parsing, scoring, suggestions, and sentence rewriting.
    """
    # 1. Matching
    match_data = match_resume_with_jd(resume_text, jd_text)
    
    # 2. Section Completeness
    sections = extract_sections(resume_text)
    section_score, section_feedback = calculate_section_completeness(sections)
    
    # 3. Final ATS Score
    ats_score = compute_ats_score(match_data, section_score)
    
    # 4. Suggestions Checklist
    recommendations = generate_recommendations(match_data, section_score, section_feedback)
    
    # 5. Sentence Optimizations
    sentence_rewrites = analyze_and_rewrite_resume(resume_text)
    
    return {
        'ats_score': ats_score,
        'text_similarity': round(match_data['text_similarity'] * 100, 1),
        'skill_overlap_score': round(match_data['skill_score'] * 100, 1),
        'matched_skills': match_data['matched_skills'],
        'missing_skills': match_data['missing_skills'],
        'resume_skills': match_data['resume_skills'],
        'section_score': section_score,
        'recommendations': recommendations,
        'sentence_rewrites': sentence_rewrites[:8]  # Limit to top 8 suggestions for UI neatness
    }

if __name__ == "__main__":
    test_resume = """
    Jane Doe
    jane.doe@gmail.com
    555-123-4567

    Education
    B.S. Software Engineering

    Experience
    Responsible for writing javascript code.
    Helped with the server development.
    Improved database query times.
    """
    
    test_jd = "Requires JavaScript, Python, PostgreSQL database management, AWS, and server deployment expertise."
    
    report = analyze_resume_full(test_resume, test_jd)
    print("ATS Score:", report['ats_score'])
    print("Matched Skills:", report['matched_skills'])
    print("Missing Skills:", report['missing_skills'])
    print("Sentence Rewrites count:", len(report['sentence_rewrites']))
    if report['sentence_rewrites']:
        print("First Rewrite:")
        print("Original:", report['sentence_rewrites'][0]['original'])
        print("Rewritten:", report['sentence_rewrites'][0]['rewritten'])
        print("Suggestions:", report['sentence_rewrites'][0]['suggestions'])
