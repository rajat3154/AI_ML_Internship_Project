import streamlit as st
import json
import random
import re
from groq import Groq
from typing import Dict, List, Any
import time

# Page configuration
st.set_page_config(
    page_title="CareerPath AI Counsellor",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E40AF;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #3B82F6;
        text-align: center;
        margin-bottom: 2rem;
    }

    .user-message {
    background-color: #01041e;
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 0 18px;
    margin: 10px 0;
    max-width: 80%;
    min-width: 20%;
    width: fit-content;
    margin-left: auto;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    word-wrap: break-word;
}

.bot-message {
    background-color: #01041e;
    color: white;
    padding: 12px 16px;

    margin: 10px 0;
    max-width: 80%;
    min-width: 20%;
    width: fit-content;
    margin-right: auto;

    box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    word-wrap: break-word;
}
    .message-symbol {
        font-weight: bold;
        margin-right: 8px;
    }
    .stButton button {
        width: 100%;
        background-color: #1E40AF;
        color: white;
        font-weight: bold;
    }
    .career-card {
        background-color: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #3B82F6;
    }
    .progress-bar {
        height: 10px;
        background-color: #E5E7EB;
        border-radius: 5px;
        margin: 10px 0;
    }
    .progress-fill {
        height: 100%;
        background-color: #10B981;
        border-radius: 5px;
        transition: width 0.5s ease-in-out;
    }
    .section-title {
        font-size: 1.2rem;
        color: #1E40AF;
        margin-top: 20px;
        margin-bottom: 10px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'conversation' not in st.session_state:
    st.session_state.conversation = []
if 'user_data' not in st.session_state:
    st.session_state.user_data = {}
if 'assessment_complete' not in st.session_state:
    st.session_state.assessment_complete = False
if 'career_recommendations' not in st.session_state:
    st.session_state.career_recommendations = []
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'api_valid' not in st.session_state:
    st.session_state.api_valid = False

# Career database
CAREER_DATABASE = {
    "technology": [
        {"name": "Software Developer", "skills": ["Programming", "Problem Solving", "Algorithms"], "growth": "22%", "salary": "$110,000"},
        {"name": "Data Scientist", "skills": ["Statistics", "Machine Learning", "Python"], "growth": "31%", "salary": "$120,000"},
        {"name": "Cybersecurity Analyst", "skills": ["Network Security", "Risk Assessment", "Ethical Hacking"], "growth": "33%", "salary": "$105,000"},
        {"name": "AI/ML Engineer", "skills": ["Machine Learning", "Python", "Deep Learning"], "growth": "40%", "salary": "$130,000"},
        {"name": "Cloud Architect", "skills": ["Cloud Computing", "Networking", "Security"], "growth": "25%", "salary": "$125,000"}
    ],
    "healthcare": [
        {"name": "Registered Nurse", "skills": ["Patient Care", "Medical Knowledge", "Empathy"], "growth": "12%", "salary": "$75,000"},
        {"name": "Physician Assistant", "skills": ["Diagnosis", "Patient Care", "Medical Knowledge"], "growth": "27%", "salary": "$115,000"},
        {"name": "Physical Therapist", "skills": ["Rehabilitation", "Anatomy", "Patient Care"], "growth": "18%", "salary": "$90,000"},
        {"name": "Medical Researcher", "skills": ["Research", "Data Analysis", "Scientific Method"], "growth": "17%", "salary": "$95,000"}
    ],
    "business": [
        {"name": "Marketing Manager", "skills": ["Strategy", "Communication", "Analytics"], "growth": "10%", "salary": "$135,000"},
        {"name": "Financial Analyst", "skills": ["Financial Modeling", "Excel", "Analysis"], "growth": "11%", "salary": "$85,000"},
        {"name": "HR Specialist", "skills": ["Recruitment", "Communication", "Employee Relations"], "growth": "10%", "salary": "$70,000"},
        {"name": "Management Consultant", "skills": ["Problem Solving", "Strategy", "Communication"], "growth": "14%", "salary": "$95,000"}
    ],
    "creative": [
        {"name": "Graphic Designer", "skills": ["Creativity", "Adobe Suite", "Visual Communication"], "growth": "5%", "salary": "$55,000"},
        {"name": "Content Writer", "skills": ["Writing", "Research", "Creativity"], "growth": "8%", "salary": "$60,000"},
        {"name": "UX/UI Designer", "skills": ["User Research", "Wireframing", "Design Thinking"], "growth": "15%", "salary": "$85,000"},
        {"name": "Video Editor", "skills": ["Editing", "Creativity", "Storytelling"], "growth": "12%", "salary": "$65,000"}
    ],
    "education": [
        {"name": "Teacher", "skills": ["Instruction", "Communication", "Patience"], "growth": "8%", "salary": "$60,000"},
        {"name": "Education Administrator", "skills": ["Leadership", "Organization", "Communication"], "growth": "7%", "salary": "$95,000"},
        {"name": "Curriculum Developer", "skills": ["Instructional Design", "Research", "Creativity"], "growth": "10%", "salary": "$70,000"}
    ]
}

# Personality questions
PERSONALITY_QUESTIONS = [
    "Do you prefer working in teams or independently?",
    "Are you more creative or analytical in your approach to problems?",
    "Do you enjoy taking leadership roles or supporting others?",
    "Do you prefer structured tasks or open-ended projects?",
    "Are you more comfortable with routine or variety in your work?",
    "Do you prefer working with people, data, or things?",
    "Are you more interested in theoretical concepts or practical applications?",
    "Do you work better under pressure or with flexible deadlines?"
]

# Initialize Groq client
def init_groq_client():
    try:
        if st.session_state.api_key:
            client = Groq(api_key=st.session_state.api_key)
            # Test the API with a simple request
            test_response = client.chat.completions.create(
                messages=[{"role": "user", "content": "Hello"}],
                model="llama-3.1-8b-instant",
                max_tokens=5
            )
            st.session_state.api_valid = True
            return client
        else:
            st.session_state.api_valid = False
            return None
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        st.session_state.api_valid = False
        return None

# Add message to conversation
def add_message(role, content):
    st.session_state.conversation.append({"role": role, "content": content})

# Generate AI response using Groq
def generate_ai_response(user_input, context):
    if not st.session_state.api_valid:
        return "Please enter a valid API key in the sidebar to use the AI features."
    
    try:
        client = init_groq_client()
        
        # Create prompt with context
        prompt = f"""
        You are a career counseling assistant. The user is exploring career options.
        
        Previous conversation context:
        {context}
        
        User's latest message: {user_input}
        
        Provide helpful, personalized career advice based on the user's interests and skills.
        Be encouraging and suggest specific career paths when appropriate.
        Keep your response concise and focused.
        """
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            max_tokens=300,
            temperature=0.7
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"I'm having trouble connecting to the AI service. Error: {str(e)}"

# Analyze user interests and recommend careers
def recommend_careers(interests, skills, personality):
    # Simple keyword-based matching
    matched_careers = []
    
    interest_keywords = {
        "technology": ["tech", "computer", "software", "programming", "code", "ai", "machine learning", "data"],
        "healthcare": ["health", "medical", "care", "doctor", "nurse", "hospital", "medicine"],
        "business": ["business", "finance", "market", "manage", "lead", "economy", "money"],
        "creative": ["creative", "design", "art", "write", "content", "video", "music"],
        "education": ["teach", "education", "learn", "school", "student", "instruct"]
    }
    
    # Score each career category based on user inputs
    category_scores = {category: 0 for category in CAREER_DATABASE.keys()}
    
    # Score based on interests
    for category, keywords in interest_keywords.items():
        for keyword in keywords:
            if keyword in interests.lower():
                category_scores[category] += 2
    
    # Score based on skills
    for category, careers in CAREER_DATABASE.items():
        for career in careers:
            for skill in career["skills"]:
                if skill.lower() in skills.lower():
                    category_scores[category] += 1
    
    # Get top categories
    top_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)[:2]
    
    # Get careers from top categories
    for category, score in top_categories:
        if score > 0:
            matched_careers.extend(CAREER_DATABASE[category])
    
    # If no matches, return some popular careers
    if not matched_careers:
        matched_careers = CAREER_DATABASE["technology"][:2] + CAREER_DATABASE["business"][:2]
    
    return matched_careers[:4]  # Return top 4 matches

# Render chat interface
def render_chat():
    st.markdown('<div class="chat-container" id="chat-container">', unsafe_allow_html=True)
    
    for message in st.session_state.conversation:
        if message["role"] == "user":
            st.markdown(f'<div class="user-message">👤 <span class="message-symbol">You:</span> {message["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="bot-message">🤖 <span class="message-symbol">CareerBot:</span> {message["content"]}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Auto-scroll to bottom
    st.markdown("""
    <script>
        function scrollToBottom() {
            const container = document.getElementById('chat-container');
            container.scrollTop = container.scrollHeight;
        }
        setTimeout(scrollToBottom, 100);
    </script>
    """, unsafe_allow_html=True)

# Personality assessment
def personality_assessment():
    st.subheader("Personality Assessment")
    st.info("Complete this quick assessment to help us understand your work preferences.")
    
    if 'personality_answers' not in st.session_state:
        st.session_state.personality_answers = [None] * len(PERSONALITY_QUESTIONS)
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    
    question_index = st.session_state.current_question
    if question_index < len(PERSONALITY_QUESTIONS):
        st.markdown(f"**{PERSONALITY_QUESTIONS[question_index]}**")
        
        # Different answer options based on question
        if question_index == 0:
            options = ["Teams", "Independently", "Both equally"]
        elif question_index == 1:
            options = ["Creative", "Analytical", "Balanced"]
        elif question_index == 2:
            options = ["Leadership roles", "Supporting others", "Depends on the situation"]
        elif question_index == 3:
            options = ["Structured tasks", "Open-ended projects", "Mix of both"]
        elif question_index == 4:
            options = ["Routine", "Variety", "Both have their place"]
        elif question_index == 5:
            options = ["People", "Data", "Things", "Combination"]
        elif question_index == 6:
            options = ["Theoretical concepts", "Practical applications", "Both"]
        else:
            options = ["Under pressure", "Flexible deadlines", "No preference"]
        
        cols = st.columns(len(options))
        for i, option in enumerate(options):
            if cols[i].button(option, key=f"q{question_index}_opt{i}", use_container_width=True):
                st.session_state.personality_answers[question_index] = option
                st.session_state.current_question += 1
                st.rerun()
        
        # Progress bar
        progress = (question_index + 1) / len(PERSONALITY_QUESTIONS)
        st.markdown(f"""
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress * 100}%"></div>
        </div>
        <div style="text-align: center; color: #6B7280; font-size: 0.9rem;">
            Question {question_index + 1} of {len(PERSONALITY_QUESTIONS)}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.success("Assessment complete! Now let's explore your career matches.")
        st.session_state.assessment_complete = True
        
        # Generate personality summary
        personality_summary = "Based on your assessment, you seem to prefer: "
        traits = []
        
        if "Independently" in st.session_state.personality_answers[0]:
            traits.append("independent work")
        if "Teams" in st.session_state.personality_answers[0]:
            traits.append("collaborative environments")
        if "Analytical" in st.session_state.personality_answers[1]:
            traits.append("analytical thinking")
        if "Creative" in st.session_state.personality_answers[1]:
            traits.append("creative problem-solving")
        
        personality_summary += ", ".join(traits) + "."
        st.session_state.user_data["personality"] = personality_summary
        
        if st.button("View Career Recommendations"):
            st.session_state.show_recommendations = True
            st.rerun()

# Display career recommendations
def display_career_recommendations():
    st.subheader("Career Recommendations")
    
    if not st.session_state.career_recommendations:
        # Generate recommendations based on user data
        interests = st.session_state.user_data.get("interests", "")
        skills = st.session_state.user_data.get("skills", "")
        
        st.session_state.career_recommendations = recommend_careers(interests, skills, 
                                                                   st.session_state.personality_answers)
    
    for career in st.session_state.career_recommendations:
        with st.container():
            st.markdown(f"""
            <div class="career-card">
                <h3>{career['name']}</h3>
                <p><strong>Key Skills:</strong> {', '.join(career['skills'])}</p>
                <p><strong>Growth Outlook:</strong> {career['growth']} (next decade)</p>
                <p><strong>Average Salary:</strong> {career['salary']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.subheader("Next Steps")
    st.info("""
    - Research these careers further to learn about day-to-day responsibilities
    - Identify skills you need to develop for your preferred path
    - Consider informational interviews with professionals in these fields
    - Explore relevant courses or certifications
    """)
    
    if st.button("Start Over"):
        # Reset conversation but keep API key
        api_key = st.session_state.api_key
        st.session_state.clear()
        st.session_state.api_key = api_key
        st.rerun()

# Main app
def main():
    st.markdown('<h1 class="main-header">CareerPath AI Counsellor</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Discover your ideal career path with AI-powered guidance</p>', unsafe_allow_html=True)
    
    # Sidebar for API key and info
    with st.sidebar:
        st.header("Configuration")
        api_key = st.text_input("Enter your Groq API Key", type="password", 
                               value=st.session_state.api_key,
                               help="Get your API key from https://console.groq.com")
        
        if api_key != st.session_state.api_key:
            st.session_state.api_key = api_key
            init_groq_client()
            st.rerun()
        
        if st.session_state.api_valid:
            st.success("✅ API key is valid")
        else:
            st.info("Please enter a valid Groq API key")
        
        st.markdown("---")
        st.header("About")
        st.info("""
        This AI career counselor helps you:
        - Discover careers that match your interests and skills
        - Understand job market trends
        - Plan your career development path
        
        Start by chatting with the AI assistant or taking the personality assessment!
        """)
    
    # Main content area
    tab1, tab2, tab3 = st.tabs(["Chat Assistant", "Personality Assessment", "Career Recommendations"])
    
    with tab1:
        st.subheader("Chat with Career Counselor")
        
        # Initialize conversation with welcome message if empty
        if not st.session_state.conversation:
            add_message("assistant", "Hello! I'm your AI career counselor. I can help you explore career options based on your interests, skills, and personality. Tell me what kind of work you're interested in!")
        
        render_chat()
        
        # Chat input
        user_input = st.chat_input("Type your message here...")
        
        if user_input:
            # Add user message to conversation
            add_message("user", user_input)
            
            # Extract user data from conversation
            if "interest" in user_input.lower() or "like" in user_input.lower() or "enjoy" in user_input.lower():
                st.session_state.user_data["interests"] = user_input
            
            if "skill" in user_input.lower() or "good at" in user_input.lower() or "experience" in user_input.lower():
                st.session_state.user_data["skills"] = user_input
            
            # Generate AI response
            with st.spinner("Thinking..."):
                # Create context from conversation history
                context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.conversation[-6:]])
                ai_response = generate_ai_response(user_input, context)
                
                # Simulate typing delay
                time.sleep(1)
                
                # Add AI response to conversation
                add_message("assistant", ai_response)
            
            st.rerun()
    
    with tab2:
        if not st.session_state.assessment_complete:
            personality_assessment()
        else:
            st.success("You've already completed the assessment!")
            if st.button("View Recommendations"):
                st.session_state.show_recommendations = True
                st.rerun()
    
    with tab3:
        if st.session_state.get("show_recommendations", False) or st.session_state.assessment_complete:
            display_career_recommendations()
        else:
            st.info("Complete the personality assessment or chat with the assistant to get career recommendations.")

if __name__ == "__main__":
    main()