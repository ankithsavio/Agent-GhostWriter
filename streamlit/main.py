import streamlit as st
import PyPDF2
import io
from typing import List, Dict
import time
import html
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AgentMessage:
    agent: str
    message: str


@dataclass
class ConversationBubble:
    title: str
    description: str
    messages: List[AgentMessage]
    background_color: str = "#2E4B7A"
    border_color: str = "#3E5B8A"


def get_agent_icon(agent_name: str) -> str:
    icons = {
        "Job Analyzer": "🤖",
        "Resume Analyzer": "🦾",
        "Matcher": "🧠",
        "Cover Letter Writer": "✍️",
        "Editor": "📝",
    }
    return icons.get(agent_name, "🤖")


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
            icon = get_agent_icon(msg.agent)
            st.markdown(
                f"""
                <div class="message-container">
                    <div class="icon-container">{icon}</div>
                    <div class="message-content">
                        <div class="agent-name" style="color: #E0E0E0;">{msg.agent}</div>
                        <div style="color: #FFFFFF;">{msg.message}</div>
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
        resume_text = ""
        if uploaded_file is not None:
            resume_text = extract_text_from_pdf(uploaded_file)
            st.success("Resume uploaded successfully!")

    if st.button("Generate Cover Letter") and job_description and resume_text:
        with st.spinner("Agents are analyzing and generating your cover letter..."):
            tab1, tab2 = st.tabs(["Agent Conversation", "Generated Cover Letter"])

            with tab1:
                st.subheader("Agent Conversation")

                analysis_bubble = create_analysis_bubble(job_description, resume_text)
                writing_bubble = create_writing_bubble()
                editing_bubble = create_editing_bubble()

                display_conversation_bubble(analysis_bubble)
                time.sleep(2)
                display_conversation_bubble(writing_bubble)
                time.sleep(2)
                display_conversation_bubble(editing_bubble)

            with tab2:
                st.subheader("Final Cover Letter")
                sample_cover_letter = """[Your Name]
                [Your Address]
                [Your Phone Number]
                [Your Email Address]

                October 26, 2023

                Atla
                [Atla's Address, if known]

                Dear Hiring Manager,

                I am writing to express my profound enthusiasm for the Machine Learning Engineer position at Atla, as advertised on [Platform where you saw the ad]. The opportunity to contribute to the scaling of fine-tuning and inference frameworks for large language models at a company like Atla, which is at the forefront of this exciting field, is incredibly compelling. My background, encompassing a robust academic foundation and practical experience, aligns perfectly with the requirements of this role, and I am confident that I can make significant contributions to your team.

                My Master's degree in AI and Machine Learning with Distinction from the University of Birmingham, combined with my Bachelor's in Computer Science, has provided me with a deep understanding of the theoretical underpinnings and practical applications of AI. During my internship as an AI/ML Intern at Nethermind, I took the initiative to develop an evaluation framework for AI agents and spearheaded the development of a video analysis tool leveraging cutting-edge technologies such as VideoLLaMA2, OpenAI Whisper, and Llama 3. This experience demonstrates my capability to develop advanced AI solutions from concept to implementation, very similar to the challenges of building an automated fine-tuning framework for large language models that Atla is currently focused on.

                My proficiency extends to a wide array of programming languages, including Python, C++, and SQL, along with deep learning frameworks like PyTorch, TensorFlow, and JAX. While I haven't directly managed multi-instance clusters for parallel training across GPUs/TPUs using Kubernetes, my project "Generative Accumulation of Photons for Inverse Problems," where I used distributed training across two T4 GPUs, demonstrates my capability in scaling machine learning models. I am also comfortable with data manipulation libraries like NumPy and Pandas, and am adept at model development using tools like HuggingFace, all of which are crucial for success in this role. Although my experience with specific orchestration systems like SLURM or Ray isn’t directly stated, my experience with containerization (Docker and Kubernetes), coupled with my distributed training knowledge, signifies an ability to adopt related technologies easily. 

                My projects, including "Brain MRI Segmentation" and "Indian Vehicle Number Plate Recognition," showcase my ability to apply diverse machine learning techniques, including transfer learning, optimization, object detection, and character recognition. The optimization work on my Brain MRI Segmentation indicates a solid foundation applicable to techniques like quantization. This wide range of experience, combined with my commitment to staying at the forefront of AI research as demonstrated by my participation in the Oxford Machine Learning Summer School and obtaining certifications in TensorFlow and Deep Learning, further reinforces my ability to develop and maintain a robust inference platform.

                Furthermore, my experience collaborating in various team environments, such as during my Data Analyst Internship and while leading the development of TruthTok's video analysis tool, demonstrates my ability to work effectively within a team and contribute to a collaborative environment. I am a strong communicator and am highly adaptable to new environments and workflows. While not explicitly described, my collaborative work and leadership in projects indicates my potential to guide and contribute to team efforts, and my experience with RESTful APIs shows I understand API design, implementation, and integration which would be useful to Atla.

                I am genuinely excited by the opportunity to contribute my skills and passion to Atla's mission. I am confident that my skills, experiences, and the demonstrated transferable skills highlighted above make me an ideal candidate for this position. I am eager to learn more about this opportunity and discuss how I can help Atla achieve its goals. Thank you for your time and consideration.

                Sincerely,

                Ankith Savio Arogya Dass
                """
                st.write(sample_cover_letter)

                st.download_button(
                    label="Download Cover Letter",
                    data=sample_cover_letter,
                    file_name="cover_letter.txt",
                    mime="text/plain",
                )

    with st.expander("How to use this tool"):
        st.write(
            """
        1. Paste the job description in the text area
        2. Upload your resume in PDF format
        3. Click 'Generate Cover Letter' to start the process
        4. Watch as our AI agents analyze and create your cover letter
        5. Download the generated cover letter
        """
        )


if __name__ == "__main__":
    main()
