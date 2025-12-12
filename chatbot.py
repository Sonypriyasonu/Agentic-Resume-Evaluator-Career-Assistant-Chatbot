import streamlit as st
import os
from resume_evaluator import ResumeEvaluator
from pii_masker import mask_resume_data
import tempfile

# Page config
st.set_page_config(
    page_title="AI-Powered Resume Evaluator & Career Assistant",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "evaluator" not in st.session_state:
    st.session_state.evaluator = ResumeEvaluator()
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""
if "job_description" not in st.session_state:
    st.session_state.job_description = ""

def add_message(role, content):
    st.session_state.messages.append({"role": role, "content": content})

def process_pdf(uploaded_file):
    """Process uploaded PDF file"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_file_path = tmp_file.name
    
    text = st.session_state.evaluator.read_pdf(tmp_file_path)
    os.unlink(tmp_file_path)
    return text

def clean_text(text):
    """Clean HTML entities and formatting issues"""
    import html
    import re
    
    # Convert to string if not already
    text = str(text)
    
    # Decode HTML entities multiple times to handle double encoding
    for _ in range(3):
        text = html.unescape(text)
    
    # Manual replacements for common entities
    replacements = {
        '&quot;': '"',
        '&#39;': "'",
        '&amp;': '&',
        '&lt;': '<',
        '&gt;': '>',
        '&nbsp;': ' '
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

# Main UI
st.title("🤖 Resume Evaluator Chatbot")
st.markdown("Upload your resume and job description to get AI-powered career insights!")

# Sidebar for inputs
with st.sidebar:
    st.header("📄 Upload Documents")
    
    # Resume upload
    st.subheader("Resume")
    resume_option = st.radio("Choose input method:", ["Upload PDF", "Paste Text"])
    
    if resume_option == "Upload PDF":
        uploaded_file = st.file_uploader("Upload Resume PDF", type="pdf")
        if uploaded_file:
            st.session_state.resume_text = process_pdf(uploaded_file)
            print(f"PDF processed, text length: {len(st.session_state.resume_text)}")
            st.success("✅ Resume uploaded!")
    else:
        resume_text = st.text_area("Paste resume text:", height=200)
        if resume_text:
            st.session_state.resume_text = resume_text
            print(f"Resume text entered, length: {len(resume_text)}")
    
    # Job description
    st.subheader("Job Description")
    job_desc = st.text_area("Paste job description:", height=200)
    if job_desc:
        st.session_state.job_description = job_desc
        print(f"Job description entered, length: {len(job_desc)}")
    
    # Evaluate button
    if st.button("🚀 Evaluate Resume", type="primary"):
        if st.session_state.resume_text and st.session_state.job_description:
            add_message("user", "Please evaluate my resume against this job description.")
            with st.spinner("🔄 AI agents are analyzing..."):
                print("Starting resume evaluation...")
                print(f"Resume text length: {len(st.session_state.resume_text)}")
                print(f"Job description length: {len(st.session_state.job_description)}")
                
                result = st.session_state.evaluator.evaluate_resume(
                    st.session_state.resume_text, 
                    st.session_state.job_description
                )
                
                print(f"Evaluation result length: {len(str(result))}")
                # Clean and format result properly
                clean_result = clean_text(result)
                add_message("assistant", f"**Evaluation Complete!** 📊\n\n{clean_result}")
        else:
            st.error("Please provide both resume and job description!")

# Chat interface
st.header("💬 Chat with Resume Evaluator")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask me about resume evaluation, career advice, or job matching..."):
    add_message("user", prompt)
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        # Always use AI for responses
        with st.spinner("🤔 AI is thinking..."):
            try:
                # Mask PII before sending to LLM
                print(f"Original resume length: {len(st.session_state.resume_text)}")
                print(f"Original JD length: {len(st.session_state.job_description)}")
                
                masked_resume, masked_jd = mask_resume_data(
                    st.session_state.resume_text, 
                    st.session_state.job_description
                )
                
                print(f"Masked resume: {masked_resume[:200]}...")
                print(f"Masked JD: {masked_jd[:200]}...")
                response = st.session_state.evaluator.chat_response(
                    prompt, 
                    masked_resume, 
                    masked_jd
                )
            except Exception as e:
                print(f"Error in chat response: {e}")
                response = "I'm here to help with career advice! What specific area would you like to discuss?"
        
        # Clean HTML entities from response
        clean_response = clean_text(response)
        
        st.markdown(clean_response)
        add_message("assistant", clean_response)

# Footer
st.markdown("---")
st.markdown("🚀 **Powered by Llama LLM + CrewAI** | Built with Streamlit")
