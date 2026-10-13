from typing import Dict, List, Set

# Comprehensive benchmarks for high-demand modern industry roles
ROLE_BENCHMARKS: Dict[str, Dict[str, List[str]]] = {
    "AI & Machine Learning Engineer": {
        "core_skills": [
            "Python", "PyTorch", "TensorFlow", "Transformers", "LLMs", "RAG",
            "LangChain", "Vector Databases", "Prompt Engineering", "Fine-Tuning",
            "NLP", "Computer Vision", "MLOps", "Docker", "Kubernetes", "FastAPI"
        ],
        "keywords": [
            "deep learning", "neural networks", "model optimization", "latency reduction",
            "embeddings", "agentic workflows", "inference", "quantization", "cuda",
            "hugging face", "scikit-learn", "data pipelines", "evaluations", "scalability"
        ],
        "action_verbs": ["Architected", "Trained", "Deployed", "Fine-tuned", "Optimized", "Scaled", "Integrated"]
    },
    "Full-Stack Software Engineer": {
        "core_skills": [
            "React", "TypeScript", "JavaScript", "Node.js", "Python", "SQL",
            "PostgreSQL", "Next.js", "REST APIs", "GraphQL", "Docker", "Git",
            "AWS", "Tailwind CSS", "Microservices", "Redis"
        ],
        "keywords": [
            "system architecture", "state management", "ci/cd", "unit testing", "tdd",
            "code quality", "performance tuning", "database design", "caching",
            "cloud infrastructure", "agile", "full-cycle development"
        ],
        "action_verbs": ["Built", "Engineered", "Designed", "Implemented", "Refactored", "Automated", "Spearheaded"]
    },
    "Data Scientist": {
        "core_skills": [
            "Python", "R", "SQL", "Pandas", "NumPy", "Scikit-Learn",
            "Data Visualization", "Tableau", "Power BI", "A/B Testing", "Statistics",
            "Predictive Modeling", "BigQuery", "Apache Spark"
        ],
        "keywords": [
            "hypothesis testing", "regression", "clustering", "exploratory data analysis",
            "feature engineering", "data cleaning", "insights", "business impact",
            "cross-functional collaboration", "kpis", "reporting"
        ],
        "action_verbs": ["Analyzed", "Derived", "Modeled", "Discovered", "Forecasted", "Identified", "Quantified"]
    },
    "Product Manager": {
        "core_skills": [
            "Product Strategy", "Roadmapping", "Agile / Scrum", "User Research",
            "Wireframing", "A/B Testing", "Data Analytics", "Cross-Functional Leadership",
            "Go-to-Market (GTM)", "PRD Creation", "Customer Discovery"
        ],
        "keywords": [
            "customer journey", "user retention", "churn reduction", "revenue growth",
            "feature prioritization", "stakeholder management", "okrs", "mvp",
            "competitive analysis", "user empathy", "metrics-driven"
        ],
        "action_verbs": ["Spearheaded", "Launched", "Prioritized", "Championed", "Defined", "Accelerated", "Scaled"]
    },
    "DevOps & Cloud Engineer": {
        "core_skills": [
            "AWS", "Azure", "GCP", "Kubernetes", "Docker", "Terraform",
            "CI/CD Pipelines", "Linux", "GitHub Actions", "Ansible", "Prometheus",
            "Grafana", "Bash", "Python", "Helm"
        ],
        "keywords": [
            "infrastructure as code (iac)", "high availability", "disaster recovery",
            "cost optimization", "zero downtime", "observability", "microservices orchestration",
            "security compliance", "automation", "site reliability engineering (sre)"
        ],
        "action_verbs": ["Automated", "Migrated", "Provisioned", "Monitored", "Orchestrated", "Hardened", "Reduced"]
    },
    "General Tech / Custom": {
        "core_skills": [
            "Leadership", "System Design", "Agile", "Cloud Computing",
            "Problem Solving", "CI/CD", "Project Management", "Data Analysis",
            "API Integration", "Collaboration", "Strategic Planning"
        ],
        "keywords": [
            "scalability", "efficiency", "revenue impact", "cross-functional",
            "deliverables", "innovation", "best practices", "continuous improvement"
        ],
        "action_verbs": ["Led", "Drove", "Delivered", "Optimized", "Transformed", "Established"]
    }
}


def analyze_role_fit(profile_text: str, current_skills: List[str], target_role: str) -> Dict:
    """
    Compares the profile text and skills against standard benchmarks for the selected target role.
    """
    benchmarks = ROLE_BENCHMARKS.get(target_role, ROLE_BENCHMARKS["General Tech / Custom"])
    all_role_skills = benchmarks["core_skills"] + benchmarks["keywords"]
    
    text_lower = profile_text.lower()
    skills_lower = [s.lower() for s in current_skills]
    
    found_skills = []
    missing_skills = []
    
    for skill in benchmarks["core_skills"]:
        if skill.lower() in skills_lower or skill.lower() in text_lower:
            found_skills.append(skill)
        else:
            missing_skills.append(skill)
            
    match_percentage = int((len(found_skills) / max(len(benchmarks["core_skills"]), 1)) * 100)
    
    return {
        "target_role": target_role,
        "match_percentage": min(match_percentage, 100),
        "found_skills": found_skills,
        "missing_skills": missing_skills,
        "recommended_action_verbs": benchmarks["action_verbs"]
    }
