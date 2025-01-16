import streamlit as st
import PyPDF2
import io
from typing import List, Dict
import time
import html
from dataclasses import dataclass
from typing import List, Optional
import os
from llms import PDFExtractor
from cover_letter_writer.utils.data import AgentMessage
from cover_letter_writer.engine import CoverLetterWriterEngine
import shutil


@dataclass
class ConversationBubble:
    title: str
    description: str
    messages: List[AgentMessage]
    background_color: str = "#2E4B7A"
    border_color: str = "#3E5B8A"


def display_conversation_bubble(bubble: ConversationBubble):
    """Display a group of related agent messages in a styled bubble"""
    st.markdown(
        """
        <style>
        .bubble-container {
            padding: 1rem;
            border-radius: 0.8rem;
            margin-bottom: 1.5rem;
            border: 2px solid;
        }
        .bubble-title {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        .bubble-description {
            font-size: 0.9rem;
            margin-bottom: 1rem;
            font-style: italic;
        }
        .message-container {
            padding: 0.8rem;
            border-radius: 0.5rem;
            margin-bottom: 0.8rem;
            display: flex;
            align-items: flex-start;
            background-color: rgba(0, 0, 0, 0.2);
        }
        .icon-container {
            font-size: 1.5rem;
            margin-right: 0.5rem;
            min-width: 2rem;
        }
        .message-content {
            flex-grow: 1;
        }
        .agent-name {
            font-weight: bold;
            margin-bottom: 0.3rem;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    with st.container():
        st.markdown(
            f"""
            <div class="bubble-container" style="background-color: {bubble.background_color}; border-color: {bubble.border_color}">
                <div class="bubble-title" style="color: #FFFFFF;">{bubble.title}</div>
                <div class="bubble-description" style="color: #E0E0E0;">{bubble.description}</div>
            """,
            unsafe_allow_html=True,
        )

        for msg in bubble.messages:
            icon = "🤖"
            message_content = msg.message.replace(
                "\n", "<br>"
            )  # Replace newlines with HTML line breaks
            st.markdown(
                f"""
                <div class="message-container">
                    <div class="icon-container">{icon}</div>
                    <div class="message-content">
                        <div class="agent-name" style="color: #E0E0E0;">{msg.agent}</div>
                        <div style="color: #FFFFFF;">{message_content}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)


def create_analysis_bubble(
    job_description: str, resume_text: str
) -> ConversationBubble:
    return ConversationBubble(
        title="Analysis Phase",
        description="Analyzing job requirements and candidate qualifications",
        messages=[
            AgentMessage(
                "Job Analyzer",
                "I've analyzed the job description. The role requires expertise in Python programming and data analysis. The company is looking for someone with strong communication skills.",
            ),
            AgentMessage(
                "Resume Analyzer",
                "Based on the resume, the candidate has 3 years of Python experience and has worked on several data analysis projects. They've also led team presentations.",
            ),
            AgentMessage(
                "Matcher",
                "There's a strong match between the job requirements and the candidate's qualifications. Key matching points: Python skills, data analysis experience, and communication abilities.",
            ),
        ],
    )

def create_writing_bubble() -> ConversationBubble:
    return ConversationBubble(
        title="Writing Phase",
        description="Drafting and refining the cover letter",
        messages=[
            AgentMessage(
                "Cover Letter Writer",
                "I'll draft a cover letter emphasizing these matching points and highlighting relevant project experiences.",
            )
        ],
        background_color="#2A4858",
        border_color="#3A5868",
    )

def create_editing_bubble() -> ConversationBubble:
    return ConversationBubble(
        title="Editing Phase",
        description="Final review and polishing",
        messages=[
            AgentMessage(
                "Editor",
                "I've reviewed and polished the cover letter, ensuring it maintains a professional tone while showcasing the candidate's enthusiasm and qualifications.",
            )
        ],
        background_color="#2A584A",
        border_color="#3A685A",
    )

def extract_text_from_pdf(pdf_file) -> str:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def main():
    temp_dir = "/mnt/c/Users/ankit/Desktop/Portfolio/automation/Agent-GhostWriter/temp"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)

    st.title("AI Cover Letter Generator")
    st.write("Generate personalized cover letters using AI agents")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Job Description")
        job_description = st.text_area(
            "Paste the job description here",
            height=300,
            placeholder="Copy and paste the job description...",
        )

    with col2:
        st.subheader("Resume")
        uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")
        if uploaded_file is not None:
            resume_text = extract_text_from_pdf(uploaded_file)
            st.success("Resume uploaded successfully!")
            resume_file_path = os.path.join(
                temp_dir,
                uploaded_file.name,
            )
            with open(resume_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        st.subheader("Cover Letter")
        uploaded_cover_letter = st.file_uploader(
            "Upload your cover letter (PDF)", type="pdf"
        )
        if uploaded_cover_letter is not None:
            cover_letter_text = extract_text_from_pdf(uploaded_cover_letter)
            st.success("Cover letter uploaded successfully!")
            letter_file_path = os.path.join(
                temp_dir,
                uploaded_file.name,
            )
            with open(letter_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

    if st.button("Generate Cover Letter") and job_description and resume_text:
        with st.spinner("Agents are analyzing and generating your cover letter..."):
            engine = CoverLetterWriterEngine(
                job_description=job_description,
                path_to_resume=resume_file_path,
                path_to_cover_letter=letter_file_path,
            )

            tab1, tab2 = st.tabs(["Agent Conversation", "Generated Cover Letter"])

            with tab1:
                st.subheader("Agent Conversation")
                job_insights = engine.get_job_insights()
                display_conversation_bubble(
                    ConversationBubble(
                        "Job Insights",
                        "Extract detailed information from the description",
                        job_insights,
                    )
                )
                resume_insights = engine.get_resume_insights()
                display_conversation_bubble(
                    ConversationBubble(
                        "Resume Insights",
                        "Extract insights from the resume tailored to the job description",
                        resume_insights,
                    )
                )
                draft_cover_letter = engine.get_cover_letter_draft()
                display_conversation_bubble(
                    ConversationBubble(
                        "Draft Generation",
                        "Generate draft based on resume and job insights",
                        draft_cover_letter,
                    )
                )
                final_cover_letter = engine.get_final_cover_letter()
                display_conversation_bubble(
                    ConversationBubble(
                        "Cover Letter Generation",
                        "Generate final cover letter based on draft and tailored critic",
                        final_cover_letter,
                    )
                )

            with tab2:
                st.subheader("Final Cover Letter")
                cover_letter = engine.final_letter
                st.write(cover_letter)

                st.download_button(
                    label="Download Cover Letter",
                    data=cover_letter,
                    file_name="cover_letter.txt",
                    mime="text/plain",
                )

    with st.expander("How to use this tool"):
        st.write(
            """
        1. Paste the job description in the text area
        2. Upload your resume in PDF format
        3. Upload your cover letter in PDF format
        4. Click 'Generate Cover Letter' to start the process
        5. Watch as our AI agents analyze and create your cover letter
        6. Download the generated cover letter in txt file
        """
        )

if __name__ == "__main__":
    main()
