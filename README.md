# Agentic-Resume-Evaluator-Career-Assistant-Chatbot
An AI-powered resume evaluation system with Streamlit frontend that supports multi-agent analysis with persistent conversation memory and comprehensive career guidance through intelligent resume-job matching.

## Capabilities

- **Persistent Memory with MongoDB**  
  Maintains conversation history across sessions using MongoDB for long-term, session-independent memory retention.

- **Multi-Agent Resume Analysis (Powered by Llama 3.3-70B via Groq API)**  
  Processes PDF and text resumes using four specialized AI agents:  
  - **Resume Parser** – Extracts structured information from resumes  
  - **Job Description Analyzer** – Understands role requirements  
  - **Skill Gap Detector** – Identifies missing or weak skill areas  
  - **Career Recommendation Specialist** – Provides tailored guidance

- **Automated PII Detection & Masking**  
  Analyzes PDF and text content to automatically detect and mask Personally Identifiable Information (PII) for secure and compliant processing.

- **Context-Aware Career Chatbot**  
  Supports ongoing career consultation with full context awareness using stored memory and prior resume/job details.

- **ATS Compatibility Scoring**  
  Calculates accurate ATS (Applicant Tracking System) compatibility scores (0–100) using AI-driven skill–job matching.

- **Actionable Career & Resume Recommendations**  
  Generates:
  - Missing skill suggestions  
  - Resume improvement tips  
  - Job-specific alignment recommendations  
  - Cover letter enhancement guidance  

---

## Purpose

- **Deliver intelligent, automated resume evaluation** with persistent contextual memory.
- **Enable seamless multi-session career guidance** through a conversational AI assistant.
- **Provide comprehensive resume analysis** paired with job-matching insights.
- **Act as a full-fledged career assistant interface**, offering resume optimization, ATS scoring, and professional recommendations with memory of past interactions.
