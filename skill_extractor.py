import re

# Categorized skills database with standard names and matching regex patterns/aliases
SKILLS_DB = {
    'Programming Languages': {
        'Python': [r'\bpython\b'],
        'JavaScript': [r'\bjavascript\b', r'\bjs\b'],
        'Java': [r'\bjava\b(?!script)'],
        'C++': [r'\bc\+\+\b', r'\bcpp\b'],
        'C#': [r'\bc#\b', r'\bc sharp\b'],
        'C': [r'\bc\b(?!\+\+)(?!#)'],
        'Ruby': [r'\bruby\b'],
        'PHP': [r'\bphp\b'],
        'Swift': [r'\bswift\b'],
        'Go': [r'\bgo\b', r'\bgolang\b'],
        'Rust': [r'\brust\b'],
        'TypeScript': [r'\btypescript\b', r'\bts\b'],
        'Kotlin': [r'\bkotlin\b'],
        'Scala': [r'\bscala\b'],
        'R': [r'\br\b'],
        'MATLAB': [r'\bmatlab\b'],
        'HTML': [r'\bhtml5?\b'],
        'CSS': [r'\bcss3?\b'],
        'Bash': [r'\bbash\b', r'\bshell script\b'],
        'SQL': [r'\bsql\b'],
        'Perl': [r'\bperl\b']
    },
    'Web Frameworks & Libraries': {
        'React': [r'\breact\b', r'\breact\.js\b', r'\breactjs\b'],
        'Angular': [r'\bangular\b', r'\bangularjs\b'],
        'Vue.js': [r'\bvue\b', r'\bvue\.js\b', r'\bvuejs\b'],
        'Node.js': [r'\bnode\b', r'\bnode\.js\b', r'\bnodejs\b'],
        'Express.js': [r'\bexpress\b', r'\bexpress\.js\b'],
        'Django': [r'\bdjango\b'],
        'Flask': [r'\bflask\b'],
        'FastAPI': [r'\bfastapi\b'],
        'Spring Boot': [r'\bspring boot\b', r'\bspring framework\b'],
        'ASP.NET': [r'\basp\.net\b', r'\b\.net\b'],
        'Laravel': [r'\blaravel\b'],
        'Ruby on Rails': [r'\bruby on rails\b', r'\brails\b'],
        'Redux': [r'\bredux\b'],
        'Next.js': [r'\bnext\.js\b', r'\bnextjs\b'],
        'Tailwind CSS': [r'\btailwind\b', r'\btailwindcss\b'],
        'Bootstrap': [r'\bbootstrap\b'],
        'jQuery': [r'\bjquery\b']
    },
    'Data Science & AI/ML': {
        'Machine Learning': [r'\bmachine learning\b', r'\bml\b'],
        'Deep Learning': [r'\bdeep learning\b', r'\bdl\b'],
        'Data Analysis': [r'\bdata analysis\b', r'\bdata analytics\b'],
        'Natural Language Processing': [r'\bnatural language processing\b', r'\bnlp\b'],
        'Computer Vision': [r'\bcomputer vision\b', r'\bcv\b'],
        'Pandas': [r'\bpandas\b'],
        'NumPy': [r'\bnumpy\b'],
        'Scikit-learn': [r'\bscikit-learn\b', r'\bsklearn\b'],
        'TensorFlow': [r'\btensorflow\b', r'\btf\b'],
        'PyTorch': [r'\bpyterm\b', r'\bpytorch\b'],
        'Keras': [r'\bkeras\b'],
        'NLTK': [r'\bnltk\b'],
        'SpaCy': [r'\bspacy\b'],
        'Scipy': [r'\bscipy\b'],
        'Tableau': [r'\btableau\b'],
        'Power BI': [r'\bpower bi\b', r'\bpowerbi\b'],
        'Apache Spark': [r'\bspark\b', r'\bapache spark\b'],
        'Hadoop': [r'\bhadoop\b'],
        'LLM': [r'\bllm\b', r'\bllms\b', r'\blarge language models\b'],
        'LangChain': [r'\blangchain\b'],
        'Hugging Face': [r'\bhugging\s*face\b', r'\bhuggingface\b']
    },
    'Databases': {
        'MySQL': [r'\bmysql\b'],
        'PostgreSQL': [r'\bpostgresql\b', r'\bpostgres\b'],
        'MongoDB': [r'\bmongodb\b', r'\bmongo\b'],
        'SQLite': [r'\bsqlite\b'],
        'Redis': [r'\bredis\b'],
        'Cassandra': [r'\bcassandra\b'],
        'Elasticsearch': [r'\belasticsearch\b'],
        'Firebase': [r'\bfirebase\b'],
        'DynamoDB': [r'\bdynamodb\b'],
        'Oracle': [r'\boracle\b'],
        'SQL Server': [r'\bsql server\b', r'\bmssql\b']
    },
    'DevOps & Cloud': {
        'Docker': [r'\bdocker\b'],
        'Kubernetes': [r'\bkubernetes\b', r'\bk8s\b'],
        'AWS': [r'\baws\b', r'\bamazon web services\b'],
        'Azure': [r'\bazure\b'],
        'Google Cloud Platform': [r'\bgcp\b', r'\bgoogle cloud\b'],
        'Git': [r'\bgit\b'],
        'GitHub': [r'\bgithub\b'],
        'GitLab': [r'\bgitlab\b'],
        'Jenkins': [r'\bjenkins\b'],
        'CI/CD': [r'\bci/cd\b', r'\bcontinuous integration\b'],
        'Terraform': [r'\bterraform\b'],
        'Ansible': [r'\bansible\b'],
        'Linux': [r'\blinux\b'],
        'Nginx': [r'\bnginx\b'],
        'Apache': [r'\bapache\b']
    },
    'Software Concepts & Methodologies': {
        'Agile': [r'\bagile\b'],
        'Scrum': [r'\bscrum\b'],
        'REST APIs': [r'\brest api\b', r'\brestful api\b', r'\brest apis\b'],
        'GraphQL': [r'\bgraphql\b'],
        'Microservices': [r'\bmicroservices\b', r'\bmicroservice\b'],
        'System Design': [r'\bsystem design\b'],
        'OOP': [r'\boop\b', r'\bobject oriented programming\b'],
        'Data Structures': [r'\bdata structures\b'],
        'Algorithms': [r'\balgorithms\b'],
        'TDD': [r'\btdd\b', r'\btest driven development\b']
    },
    'Soft Skills': {
        'Communication': [r'\bcommunication skills\b', r'\bcommunication\b', r'\bwritten and verbal\b'],
        'Leadership': [r'\bleadership\b', r'\bteam leading\b', r'\bmentorship\b'],
        'Problem Solving': [r'\bproblem solving\b', r'\banalytical skills\b'],
        'Teamwork': [r'\bteamwork\b', r'\bcollaboration\b', r'\bteam player\b'],
        'Time Management': [r'\btime management\b', r'\borganizational skills\b'],
        'Critical Thinking': [r'\bcritical thinking\b'],
        'Adaptability': [r'\badaptability\b', r'\badaptable\b']
    }
}

# Flattens skills database for quick lookup mapping alias -> standard skill
ALL_SKILLS_FLAT = []
for category, skills in SKILLS_DB.items():
    for skill_name, patterns in skills.items():
        ALL_SKILLS_FLAT.append({
            'name': skill_name,
            'category': category,
            'patterns': [re.compile(p, re.IGNORECASE) for p in patterns]
        })

def extract_skills(text):
    """
    Scans text against the skills database and extracts matching skills.
    Returns:
        A dict matching: {'skills': [list of skill names], 'categories': {category: [list of skills]}}
    """
    if not text:
        return {'skills': [], 'categories': {}}
        
    matched_skills = set()
    categorized_matches = {}
    
    # Process text matching
    for skill_item in ALL_SKILLS_FLAT:
        name = skill_item['name']
        category = skill_item['category']
        patterns = skill_item['patterns']
        
        # Exception for very short common words (e.g. "C", "R", "Go")
        # Ensure we only match if they have specific context or clear boundaries
        is_short_or_ambiguous = name in ['C', 'R', 'Go']
        
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                if is_short_or_ambiguous:
                    # For Go, R, C, let's check if they appear close to other technical terms or in specific context.
                    # Or check that they are capitalized in raw text (since our standard clean_text lowercases everything,
                    # we can examine the original casing if we want, or rely on double boundary matching)
                    # Let's enforce strict word boundaries. Since we used \bc\b etc., it's already bounded.
                    # However, to reduce false positives for single letters 'C' or 'R', we can see if other keywords
                    # like 'programming', 'developer', 'code', 'software', or database systems are present.
                    text_lower = text.lower()
                    tech_context = any(term in text_lower for term in ['software', 'developer', 'programming', 'skills', 'engineer', 'technologies'])
                    if not tech_context:
                        continue # Skip to avoid matching common text references
                
                matched_skills.add(name)
                if category not in categorized_matches:
                    categorized_matches[category] = set()
                categorized_matches[category].add(name)
                break # Matched this skill, move to next
                
    # Convert sets to sorted lists
    sorted_skills = sorted(list(matched_skills))
    sorted_categorized = {cat: sorted(list(skills)) for cat, skills in categorized_matches.items()}
    
    return {
        'skills': sorted_skills,
        'categories': sorted_categorized
    }

if __name__ == "__main__":
    test_resume = """
    Software Developer Resume
    I develop using Python, JavaScript, and C++. I have experience with Django and React.
    Databases: MongoDB and PostgreSQL. I use AWS for cloud hosting and Docker for containerization.
    Strong communication skills and problem solving.
    """
    
    res = extract_skills(test_resume)
    print("Skills Matched:")
    print(res['skills'])
    print("\nCategorized:")
    import json
    print(json.dumps(res['categories'], indent=2))
