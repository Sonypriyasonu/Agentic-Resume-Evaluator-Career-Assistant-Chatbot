import re

def mask_resume_data(resume_text, job_description):
    """
    Mask PII (Personally Identifiable Information) from resume and job description
    """
    
    def mask_text(text):
        if not text:
            return ""
        
        # Email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        
        # Phone numbers (various formats)
        text = re.sub(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', '[PHONE]', text)
        text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]', text)
        text = re.sub(r'\b\(\d{3}\)\s?\d{3}-\d{4}\b', '[PHONE]', text)
        
        # Addresses (basic pattern)
        text = re.sub(r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)', '[ADDRESS]', text, flags=re.IGNORECASE)
        
        # Social Security Numbers
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]', text)
        
        # ZIP codes
        text = re.sub(r'\b\d{5}(-\d{4})?\b', '[ZIP]', text)
        
        return text
    
    masked_resume = mask_text(resume_text)
    masked_jd = mask_text(job_description)
    
    return masked_resume, masked_jd
