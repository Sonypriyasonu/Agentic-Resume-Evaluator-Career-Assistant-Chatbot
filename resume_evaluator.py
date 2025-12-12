import os
import re
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Task, Crew, Process
from crewai.llm import LLM
from pymongo import MongoClient
import PyPDF2
from pii_masker import mask_resume_data

load_dotenv()

llm = LLM(
    model="groq/llama-3.3-70b-versatile",
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

class ResumeEvaluator:
    def __init__(self):
        # MongoDB setup
        self.client = MongoClient('mongodb://localhost:27017/')
        self.db = self.client['career_assistant_db']
        self.collection = self.db['chat_history']
        self.agents = self._create_agents()
    
    def save_conversation(self, question, response, conversation_type="chat"):
        """Save conversation to MongoDB"""
        try:
            document = {
                "timestamp": datetime.now(),
                "type": conversation_type,
                "question": question,
                "response": response
            }
            self.collection.insert_one(document)
        except Exception as e:
            print(f"Error saving conversation: {e}")
    
    def get_all_conversations(self):
        """Get all conversations for full context"""
        try:
            conversations = list(self.collection.find({}, {'_id': 0}).sort('timestamp', 1))
            return conversations
        except Exception as e:
            print(f"Error loading conversations: {e}")
            return []
    
    def _create_agents(self):
        # Resume Parsing Agent
        resume_parser = Agent(
            role='Resume Parser',
            goal='Extract and structure key information from resumes',
            backstory='Expert at parsing resumes and extracting skills, experience, education',
            llm=llm,
            verbose=True
        )
        
        # Job Description Analysis Agent
        jd_analyzer = Agent(
            role='Job Description Analyzer',
            goal='Analyze job descriptions and extract requirements',
            backstory='Specialist in understanding job requirements and qualifications',
            llm=llm,
            verbose=True
        )
        
        # Skill Gap Detection Agent
        skill_gap_detector = Agent(
            role='Skill Gap Detector',
            goal='Identify missing skills and calculate ATS compatibility',
            backstory='Expert at comparing candidate profiles with job requirements',
            llm=llm,
            verbose=True
        )
        
        # Recommendation Agent
        recommendation_agent = Agent(
            role='Career Recommendation Specialist',
            goal='Provide actionable recommendations and generate improved content',
            backstory='Career coach specializing in resume optimization and salary insights',
            llm=llm,
            verbose=True
        )
        
        return {
            'parser': resume_parser,
            'analyzer': jd_analyzer,
            'detector': skill_gap_detector,
            'recommender': recommendation_agent
        }
    
    def clean_text(self, text):
        """Remove code block formatting from text"""
        text = str(text)
        text = text.replace('```text', '').replace('```', '')
        return text.strip()
    
    def read_pdf(self, file_path):
        """Extract text from PDF resume"""
        try:
            with open(file_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text()
                return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def evaluate_resume(self, resume_text, job_description):
        """Main evaluation process"""
        
        # Mask PII before processing
        masked_resume, masked_jd = mask_resume_data(resume_text, job_description)
        
        # Task 1: Parse Resume
        parse_task = Task(
            description=f"""
            Parse this resume and extract:
            - Personal information
            - Skills (technical and soft)
            - Work experience
            - Education
            - Certifications
            
            Resume: {masked_resume}
            """,
            agent=self.agents['parser'],
            expected_output="Clear summary of candidate's skills, experience, and qualifications in readable text"
        )
        
        # Task 2: Analyze Job Description
        analyze_task = Task(
            description=f"""
            Analyze this job description and extract:
            - Required skills
            - Preferred qualifications
            - Experience requirements
            - Education requirements
            
            Job Description: {masked_jd}
            """,
            agent=self.agents['analyzer'],
            expected_output="Clear summary of job requirements and qualifications in readable text"
        )
        
        # Task 3: Detect Skill Gaps
        gap_task = Task(
            description="""
            Compare the parsed resume with job requirements and calculate precise scores:
            
            CRITICAL: You MUST provide an exact ATS compatibility score as a number between 0-100.
            
            Calculate based on:
            - Skills match (40% weight)
            - Experience relevance (30% weight) 
            - Education alignment (20% weight)
            - Keywords presence (10% weight)
            
            Provide:
            - **ATS Score: [EXACT NUMBER]/100** (e.g., ATS Score: 75/100)
            - Missing skills list (top 5)
            - Matching percentage for overall fit
            - Areas of strength
            
            IMPORTANT: Always include "ATS Score: [NUMBER]/100" in your response.
            """,
            agent=self.agents['detector'],
            expected_output="Skill gap analysis with exact ATS score (0-100), missing skills, and match percentage",
            context=[parse_task, analyze_task]
        )
        
        # Task 4: Generate Recommendations
        recommend_task = Task(
            description="""
            Write a career recommendation report in PLAIN TEXT format (NOT JSON).
            
            CRITICAL: Include the ATS score from the skill gap analysis at the top.
            
            Structure it like this:
            
            ### Career Recommendations
            
            **ATS Compatibility Score: [EXTRACT FROM PREVIOUS ANALYSIS]/100**
                        
            **Top Missing Skills:**
            1. Skill 1
            2. Skill 2
            3. Skill 3
            4. Skill 4
            5. Skill 5
            
            **Resume Improvements:**
            - Suggestion 1
            - Suggestion 2
            - Suggestion 3
            
            **Cover Letter Tips:**
            - Tip 1
            - Tip 2
            - Tip 3
            
            **ATS Optimization:**
            - Use keywords from job description
            - Simple formatting
            - Standard section headings
            
            IMPORTANT: Extract and display the exact ATS score from the skill gap analysis. Write in readable text format, NOT JSON.
            """,
            agent=self.agents['recommender'],
            expected_output="Career report with ATS score, missing skills, and recommendations in markdown format",
            context=[parse_task, analyze_task, gap_task]
        )
        
        # Create and run crew
        crew = Crew(
            agents=list(self.agents.values()),
            tasks=[parse_task, analyze_task, gap_task, recommend_task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        clean_result = self.clean_text(result)
        
        # Save evaluation results to memory
        self.save_conversation(
            f"Resume evaluation for job: {job_description[:100]}...",
            clean_result,
            "evaluation"
        )
        
        return clean_result
    
    def chat_response(self, question, resume_text="", job_description=""):
        """Generate chatbot responses for career questions"""
        chat_agent = Agent(
            role='Career Chatbot',
            goal='Provide helpful career advice and resume guidance',
            backstory='Friendly career advisor specializing in resume optimization and job search',
            llm=llm,
            verbose=False
        )
        
        # Get all previous conversations for full context
        all_conversations = self.get_all_conversations()
        conversation_history = ""
        if all_conversations:
            conversation_history = "\nPrevious conversation history:\n"
            for conv in all_conversations:
                conversation_history += f"Q: {conv['question']}\nA: {conv['response']}\n\n"
        
        context = ""
        if resume_text:
            context += f"\nFull Resume Details: {resume_text}"
        if job_description:
            context += f"\nJob Description: {job_description}"
        context += conversation_history
        
        # Check if this is a new user (no conversation history)
        is_new_user = len(all_conversations) == 0
        greeting_context = ""
        if is_new_user and any(word in question.lower() for word in ['hi', 'hello', 'hey', 'greetings']):
            greeting_context = "\nThis is a new user saying hello. Start with: 'Welcome to your AI Career Assistant! I'm here to help you with resume optimization, job matching, and career guidance.'"
        
        chat_task = Task(
            description=f"""
            You are a professional AI Career Assistant. Respond in a professional, helpful, and knowledgeable manner.
            
            Question: {question}
            {context}
            {greeting_context}
            
            Guidelines:
            - Be professional and courteous
            - Do not show your thinking process or use phrases like "Thought:" or "I now can"
            - Provide only the final answer in a conversational tone (2-3 sentences max). Ask a follow-up question.
            """,
            agent=chat_agent,
            expected_output="Professional career guidance response"
        )
        
        crew = Crew(
            agents=[chat_agent],
            tasks=[chat_task],
            process=Process.sequential,
            verbose=False
        )
        
        result = crew.kickoff()
        # Extract and clean text from result
        if hasattr(result, 'raw'):
            text = result.raw
        elif hasattr(result, 'text'):
            text = result.text
        else:
            text = str(result)
        
        # Clean HTML entities and format properly
        import html
        text = html.unescape(text)
        
        # Remove "Thought:" patterns that sometimes appear
        text = re.sub(r'Thought:.*?(?=\n|$)', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^\s*Thought:.*?\n', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        response = text.strip()
        
        # Save conversation to local storage
        self.save_conversation(question, response)
        
        return response

def main():
    evaluator = ResumeEvaluator()
    
    print("=== Intelligent Resume Evaluator ===\n")
    
    # Get inputs
    resume_option = input("Enter '1' for PDF file or '2' for text input: ")
    
    if resume_option == '1':
        resume_path = input("Enter resume PDF path: ")
        resume_text = evaluator.read_pdf(resume_path)
    else:
        print("Paste your resume text (press Enter twice when done):")
        lines = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)
        resume_text = "\n".join(lines)
    
    print("\nPaste the job description (press Enter twice when done):")
    jd_lines = []
    while True:
        line = input()
        if line == "":
            break
        jd_lines.append(line)
    job_description = "\n".join(jd_lines)
    
    # Evaluate resume
    print("\n🔄 Evaluating resume...")
    result = evaluator.evaluate_resume(resume_text, job_description)
    print("\n" + "="*50)
    print("EVALUATION RESULTS")
    print("="*50)
    print(result)

if __name__ == "__main__":
    main()
