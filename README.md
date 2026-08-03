Markdown
# AI Pull Request Reviewer

An automated code review agent integrated into GitHub Actions. It captures diffs from Pull Requests, runs static/linguistic code analysis using the Groq Llama 3.3 model with structured output enforcement (Pydantic v2), and posts comprehensive review summaries directly to the PR timeline.

## Overview

<pre>
PR Created / Updated
       │
       ▼
GitHub Actions Workflow
       │
       ▼
review_pr.py (Fetches Diff & Runs Checks)
       │
       ▼
Groq API (Llama-3.3-70b via System Schema)
       │
       ▼
Pydantic v2 Validation
       │
       ▼
PR Comment Posted via GitHub API
</pre>

## Example Review

![AI Reviewer Example](docs/assets/review-demo.png)

## Features

- **Sub-Second Reviews**: Uses Groq's API engine (`llama-3.3-70b-versatile`) for low-latency feedback.
- **Strict Schema Enforcement**: Validates model output using Pydantic v2 to guarantee structured JSON responses.
- **Automated Workflow**: Triggers automatically on `pull_request` events (`opened`, `synchronize`).
- **Comprehensive Analysis**: Evaluates security risks, code formatting, potential bugs, and performance improvements.

## Architecture & Tech Stack

- **Runtime**: Python 3.10+
- **Inference Engine**: Groq API
- **Schema Validation**: Pydantic v2
- **GitHub Integration**: PyGithub / GitHub REST API v3
- **CI/CD**: GitHub Actions

## Project Structure

<pre>
.
├── .github/
│   └── workflows/
│       └── ai-review.yml    # CI/CD trigger on PR events
├── docs/
│   └── assets/              # Screenshots and demo media
├── review_pr.py              # Main review engine and API orchestrator
├── requirements.txt          # Python dependencies
├── .gitignore
└── README.md
</pre>

## Setup & Local Testing

### Prerequisites

- Python 3.10 or higher
- A [Groq API Key](https://console.groq.com/)
- A GitHub Personal Access Token (for local API testing)

### Local Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/ai-pr-reviewer.git
cd ai-pr-reviewer
Set up a virtual environment and install dependencies:

Bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Configure environment variables (create a .env file for local development):

Code snippet
GROQ_API_KEY=your_groq_api_key
GITHUB_TOKEN=your_github_token
PR_NUMBER=1
Run local test execution:

Bash
python review_pr.py
GitHub Actions Configuration
To enable automated reviews on repository Pull Requests:

Navigate to Settings > Secrets and variables > Actions in your repository.

Create a new Repository Secret named GROQ_API_KEY and paste your API key.

Verify .github/workflows/ai-review.yml is on your default branch.

License
Distributed under the MIT License.