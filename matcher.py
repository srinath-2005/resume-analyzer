from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nlp_utils import preprocess_text
from skill_extractor import extract_skills

def calculate_cosine_similarity(text1, text2):
    """
    Computes TF-IDF cosine similarity between two texts.
    Preprocesses the texts first.
    """
    cleaned_t1 = preprocess_text(text1)
    cleaned_t2 = preprocess_text(text2)
    
    # If one of the texts is empty after preprocessing
    if not cleaned_t1 or not cleaned_t2:
        return 0.0
        
    try:
        vectorizer = TfidfVectorizer()
        tfidf = vectorizer.fit_transform([cleaned_t1, cleaned_t2])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return float(sim)
    except Exception as e:
        print(f"Error computing cosine similarity: {e}")
        return 0.0

def match_resume_with_jd(resume_text, jd_text):
    """
    Detailed match of resume with job description.
    Extracts text similarity, matching skills, and missing skills.
    """
    # 1. Compute general cosine similarity
    text_sim = calculate_cosine_similarity(resume_text, jd_text)
    
    # 2. Extract skills from both texts
    resume_skills_info = extract_skills(resume_text)
    jd_skills_info = extract_skills(jd_text)
    
    resume_skills = set(resume_skills_info['skills'])
    jd_skills = set(jd_skills_info['skills'])
    
    # 3. Calculate skill overlap
    matched_skills = resume_skills.intersection(jd_skills)
    missing_skills = jd_skills.difference(resume_skills)
    
    if len(jd_skills) > 0:
        skill_score = len(matched_skills) / len(jd_skills)
    else:
        # If the job description lists no explicit known skills, match score defaults to 1.0 (or we rely on text_sim)
        skill_score = 1.0
        
    return {
        'text_similarity': text_sim,
        'skill_score': skill_score,
        'resume_skills': list(resume_skills),
        'jd_skills': list(jd_skills),
        'matched_skills': list(matched_skills),
        'missing_skills': list(missing_skills)
    }

if __name__ == "__main__":
    test_resume = "Skilled Python and Javascript developer. Knows Django, Flask, Postgres, and Docker."
    test_jd = "Looking for a Software Engineer with Python, React, Postgres, and Kubernetes skills."
    
    res = match_resume_with_jd(test_resume, test_jd)
    print("Match Results:")
    print(f"Text Cosine Similarity: {res['text_similarity']:.2f}")
    print(f"Skill Score: {res['skill_score']:.2f}")
    print(f"Matched Skills: {res['matched_skills']}")
    print(f"Missing Skills: {res['missing_skills']}")
