# Agentic Ghost Writer
Orchestrating LLM Personas to provide personalized CV suggestions


## Overview
Agentic Ghost Writer is a multi-persona AI Workflow that can drastically improve your job application strategy. It provides personalized reports on how to improve your CV and Cover Letter for any job role. It uses web search and autonomous information seeking conversations to tailor the reports for your documents.


## Key Features
- Inter-Persona Communication: Adapts Knowledge Storm to orchestrate communications grounded on user documents.

- Autonomous Web Search: Utilizes Search API to retrieve latest data from the Internet.

- Optional Completely Local Setup: Supports Ollama and SearXNG deployments for complete privacy on your documents.

- Interactive and Transparent UI: Simple and intuitive UI to upload necessary documents and view the working of the main system features live.



## Why use this tool?
- Crafting CV and Cover Letter is highly time consuming. This project is NOT for writing these documents from scratch but instead for aiding you to make this process faster with the help of structures reports that suggest how to adapt your documents for different job applications. Doing it this way preserves the highly important personal-touch of the users that companies sought out for.
- The project is open source and can be self hosted to use it for free by following some guidelines [mentioned below]. It is designed to be quick and manage your personal free-quota gracefully.
- It is highly configurable with minimal changes to config files. The default settings take approximately ~5mins to generate reports and the users can increase or decrease this duration with a trade-off for accuracy. Configuration customization details are [mentioned below].




## Setup
### Prerequisites
Python version: 3.10

Install uv python manager : pip install uv

Install Docker

LLM providers: supports OpenAI, Gemini, Groq, Huggingface Inference and Togetherai
Togetherai Approach(Recommended):

Goto this [website] and get your API key to use meta/meta-llama-3.3-70b-free (default)

Web Search providers: supports Google Custom Search, Searxng and DuckDuckGO(langchain_community)
	Google Custom Search Approach (Recommended):
	Goto this [website] and get you API key and create you engine copy [cx] and [key]

Set your environment variable: .env.example -> .env code


### Installation

Docker :
Setup the project and access the UI through localhost:3000
Docker compose up



### Configurations:

config/llms.yaml
	llm: 
	
	structllm: 

	ollama:

config/ghost_writer.yaml
	engine:

	knowledge_builder:

self-host all services:
	ollama in config/llms.yaml
		download ollama

	docker-compose.web.yml


## Usage

Video

      Inputs

      Outputs


## Architecture
System Diagram

	More detailed diagram



Component Breakdown

	backend
      engine.py
	
	ghost_writer
		vectordb.py
		search.py
		knowledgebasebuilder.py
		storm.py

		


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
   PYTHONPATH=
   GEMINI_API_KEY=
   TOGETHER_API_KEY=
   MONGO_ROOT_USERNAME=
   MONGO_ROOT_PASSWORD=
   GOOGLE_WEB_API_KEY=
   GOOGLE_WEB_CX=
   ```

## Dataflow Diagram

![Figure](ghost_writer_figure.png)
