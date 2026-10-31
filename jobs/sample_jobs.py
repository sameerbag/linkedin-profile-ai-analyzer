from typing import List
from .models import JobPosting

SAMPLE_JOBS: List[JobPosting] = [
    JobPosting(
        id="job-ai-001",
        title="Senior AI / Machine Learning Engineer",
        company="ScaleAI Labs",
        location="San Francisco, CA (Hybrid / Remote)",
        country="USA",
        city="San Francisco",
        is_remote=True,
        job_type="Full-time",
        job_url="https://www.linkedin.com/jobs/view/sample-ai-001",
        source="LinkedIn",
        salary="$160,000 - $210,000 / yr",
        date_posted="2 days ago",
        description="""We are looking for a Senior AI / Machine Learning Engineer to design, fine-tune, and deploy state-of-the-art LLM pipelines and autonomous agentic workflows.

Responsibilities:
• Architect scalable Retrieval-Augmented Generation (RAG) pipelines and vector search indexing.
• Fine-tune open-weights models (Llama 3, Mistral) using LoRA/QLoRA and quantize models for low-latency inference.
• Deploy microservices on Kubernetes using Docker, FastAPI, and Triton Inference Server.
• Optimize model latency, throughput, and GPU utilization across AWS and GCP clusters.

Required Qualifications:
• 4+ years of software engineering experience with strong proficiency in Python and PyTorch.
• Hands-on production experience with LLMs, Transformers, RAG, LangChain or LlamaIndex, and Vector Databases (Pinecone, Qdrant, Milvus).
• Experience deploying machine learning applications using Docker, Kubernetes, and CI/CD pipelines.
• Strong foundation in system design, distributed systems, and REST API architecture."""
    ),
    JobPosting(
        id="job-fs-002",
        title="Staff Full-Stack Software Engineer",
        company="CloudScale Technologies",
        location="Bengaluru, Karnataka, India (Remote / Hybrid)",
        country="India",
        city="Bengaluru",
        is_remote=True,
        job_type="Full-time",
        job_url="https://www.linkedin.com/jobs/view/sample-fs-002",
        source="LinkedIn",
        salary="₹35,00,000 - ₹50,00,000 / yr",
        date_posted="1 day ago",
        description="""CloudScale is seeking a Staff Full-Stack Software Engineer to spearhead our next-generation enterprise SaaS platform.

Responsibilities:
• Lead full-lifecycle frontend and backend feature engineering from conceptualization to global production release.
• Build lightning-fast, reactive user interfaces in React, TypeScript, and Next.js.
• Engineer resilient, high-concurrency microservices with Python (FastAPI/Django) and Node.js.
• Design robust relational schemas in PostgreSQL and optimize query performance with Redis caching.

Required Qualifications:
• 5+ years of full-stack engineering experience.
• Mastery of React, TypeScript, Modern JavaScript, and state management.
• Deep expertise with Python (FastAPI/Flask) or Node.js backend services.
• Experience with cloud deployments on AWS or Azure, Docker containerization, and automated testing (Jest, PyTest)."""
    ),
    JobPosting(
        id="job-ds-003",
        title="Lead Data Scientist & Predictive Modeler",
        company="FinMetrics Global",
        location="New York, NY (On-site / Hybrid)",
        country="USA",
        city="New York",
        is_remote=False,
        job_type="Full-time",
        job_url="https://www.indeed.com/viewjob?jk=sample-ds-003",
        source="Indeed",
        salary="$150,000 - $190,000 / yr",
        date_posted="3 days ago",
        description="""FinMetrics is hiring a Lead Data Scientist to discover actionable insights and build predictive risk scoring models across millions of daily financial transactions.

Responsibilities:
• Develop predictive regression, classification, and time-series models using Python, Scikit-Learn, and XGBoost.
• Write complex analytical SQL queries in BigQuery and Snowflake for feature engineering.
• Design and evaluate rigorous A/B experiments to measure business KPIs and user conversion impact.
• Translate quantitative data findings into strategic executive presentations.

Required Qualifications:
• 4+ years in Data Science, Statistics, or Quantitative Analytics.
• Expert proficiency in Python, Pandas, NumPy, SQL, and data visualization (Tableau, Plotly).
• Proven track record of launching machine learning models into live production environments."""
    ),
    JobPosting(
        id="job-devops-004",
        title="DevOps & Site Reliability Engineer (SRE)",
        company="Apex Infrastructure",
        location="London, United Kingdom (Remote)",
        country="United Kingdom",
        city="London",
        is_remote=True,
        job_type="Full-time",
        job_url="https://www.glassdoor.com/job-listing/sample-devops-004",
        source="Glassdoor",
        salary="£85,000 - £110,000 / yr",
        date_posted="Just now",
        description="""Apex Infrastructure is looking for a DevOps/SRE Engineer to maintain 99.99% uptime across multi-region cloud systems.

Responsibilities:
• Manage multi-cloud infrastructure as code (IaC) using Terraform and Ansible.
• Administer production Kubernetes clusters (EKS/GKE), Helm charts, and service meshes.
• Build and maintain zero-downtime CI/CD pipelines via GitHub Actions and GitLab CI.
• Implement observability, alerting, and distributed tracing with Prometheus, Grafana, and Datadog.

Required Qualifications:
• 3+ years managing production infrastructure on AWS or GCP.
• Deep operational knowledge of Kubernetes, Docker, and Linux internals.
• Scripting experience in Python or Bash.
• Experience with security compliance and disaster recovery architectures."""
    ),
    JobPosting(
        id="job-pm-005",
        title="Technical Product Manager - AI Platforms",
        company="NextGen Innovations",
        location="Toronto, ON, Canada (Hybrid)",
        country="Canada",
        city="Toronto",
        is_remote=False,
        job_type="Full-time",
        job_url="https://www.ziprecruiter.com/jobs/sample-pm-005",
        source="ZipRecruiter",
        salary="CAD $130,000 - $165,000 / yr",
        date_posted="4 days ago",
        description="""We are looking for a Technical Product Manager to drive product strategy and execution for our developer platform and generative AI APIs.

Responsibilities:
• Define product roadmap, PRDs, and user stories for developer tooling and AI capabilities.
• Lead cross-functional alignment between engineering, design, marketing, and sales leadership.
• Analyze user behavior metrics and customer telemetry to optimize product retention and growth.
• Prioritize sprint backlogs using Agile/Scrum ceremonies.

Required Qualifications:
• 3+ years of product management experience in B2B SaaS, developer APIs, or AI products.
• Technical background or strong ability to collaborate deeply with software engineers.
• Data-driven mindset with experience in A/B testing, user journey mapping, and KPI tracking."""
    ),
    JobPosting(
        id="job-genai-006",
        title="Generative AI Application Developer",
        company="Hyperion AI",
        location="Berlin, Germany (Remote in Europe)",
        country="Germany",
        city="Berlin",
        is_remote=True,
        job_type="Full-time",
        job_url="https://remoteok.com/l/sample-genai-006",
        source="RemoteOK",
        salary="€80,000 - €105,000 / yr",
        date_posted="1 day ago",
        description="""Hyperion AI is building context-aware enterprise co-pilots. We need a Generative AI Developer to integrate LLM foundation models into real-world workflows.

Responsibilities:
• Implement agentic workflows, multi-agent frameworks (AutoGen, CrewAI, LangGraph), and tools integration.
• Optimize embeddings, semantic caching, and chunking strategies in Vector DBs.
• Build secure, authenticated FastAPI backends with robust prompt injection defense.

Required Qualifications:
• Strong programming skills in Python and TypeScript.
• Experience with OpenAI, Anthropic, Gemini APIs, or open-source HuggingFace models.
• Familiarity with Docker, Git, and automated testing."""
    )
]
