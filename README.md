# Model Card Auditor – Chrome Extension 

Evaluate Hugging Face model cards directly in your browser and receive a structured audit powered by GPT. This plugin analyzes documentation completeness, standards coverage, governance rigor, reproducibility, risk transparency, and more.

## Features

* Click-to-evaluate model card (does not auto-trigger)
* Detailed audit panel
* Floating evaluator widget:

Click to open full audit panel.
GPT runs at temperature = 0 for deterministic output (minimal hallucination). 
Backend provides both structured JSON and full Markdown audit.

## Installation & Setup

1. Clone the repository:

`git clone <insert URL>`

3. Create .env file

Create a file named .env in the same directory as server.py:
```
OPENAI_API_KEY=<your_openai_key_here>
OPENAI_MODEL=gpt-4o
```

3. Install backend dependencies

`pip install fastapi uvicorn python-dotenv openai requests beautifulsoup4` (or pip3 install ...)

5. Start the backend
   
`python server.py` (or python3 server.py)

7. Installing the Chrome Extension

a) Open Chrome → Extensions

b) Enable Developer Mode

c) Click Load unpacked

d) Select the chrome-plugin/ folder

e) Visit any Hugging Face model card page

The floating “Evaluate Model Card” button will appear in the bottom-right corner.

## Usage

1. Open a Hugging Face model card page

2. Click “Evaluate Model Card”

3. Wait for the spinner to finish

4. Once grading completes, the button glows

5. Click again to view the full audit panel


