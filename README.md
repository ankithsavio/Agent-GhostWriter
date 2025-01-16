# Cover Letter AI Agent

## Setup and Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/ankithsavio/Agent-GhostWriter.git
   cd Agent-GhostWriter
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Configure API keys in a `.env` file:
   ```env
   HF_API_KEY=your_huggingface_api_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

## Usage
   Run the streamlit app:
   ```bash
   python -m streamlit run app/main.py --server.headless true
   ```


