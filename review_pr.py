import json
import os
import re
import sys
from typing import List
from dotenv import load_dotenv
from github import Auth, Github
from groq import Groq
from pydantic import BaseModel, Field

load_dotenv()

MAX_DIFF_CHARS = 12000  # Guard against token overflow on large PRs

class InlineComment(BaseModel):
    file_path: str = Field(description="Relative path of the file being reviewed.")
    line_number: int = Field(description="Line number in the diff/patch where the comment applies.")
    comment: str = Field(description="Actionable, constructive feedback or fix suggestion.")

class PRReviewResult(BaseModel):
    summary: str = Field(description="High-level summary of changes and overall code quality.")
    overall_score: int = Field(description="Score out of 10 evaluating readiness to merge.")
    key_issues: List[str] = Field(description="List of critical bugs, security risks, or anti-patterns.")
    inline_comments: List[InlineComment] = Field(description="File-specific inline suggestions.")

groq_api_key = os.getenv("GROQ_API_KEY")
github_token = os.getenv("GITHUB_TOKEN")
repo_name = os.getenv("GITHUB_REPOSITORY")
pr_number_str = os.getenv("PR_NUMBER")

if not groq_api_key:
    print("Error: GROQ_API_KEY is missing from environment variables.")
    sys.exit(1)

# Added timeout and retries to prevent connection blips
groq_client = Groq(
    api_key=groq_api_key,
    timeout=30.0,
    max_retries=2,
)

def clean_json_response(raw_text: str) -> str:
    """Strips Markdown backticks and extracts pure JSON text."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
    return cleaned.strip()

def run_review():
    # Local mock mode for safe offline testing
    if not (github_token and repo_name and pr_number_str):
        print("Notice: GitHub environment variables missing. Running in local test mode...\n")
        mock_diff = """
        diff --git a/app.py b/app.py
        index 83258fe..14d9a21 100644
        --- a/app.py
        +++ b/app.py
        @@ -5,3 +5,5 @@ def get_user_data(user_id):
        -    query = "SELECT * FROM users WHERE id = " + str(user_id)
        +    # SQL Injection risk
        +    query = f"SELECT * FROM users WHERE id = {user_id}"
             return db.execute(query)
        """
        review_data = process_pr_review(mock_diff)
        if review_data:
            print("--- LOCAL REVIEW TEST SUCCESSFUL ---")
            print(format_github_comment(review_data))
            print("Inline Comments Generated:", len(review_data.inline_comments))
        return

    # Production GitHub Actions mode (using Auth.Token to avoid deprecation warning)
    auth = Auth.Token(github_token)
    gh = Github(auth=auth)
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(int(pr_number_str))

    print(f"Fetching diff for PR #{pr.number}: {pr.title}")
    
    files = pr.get_files()
    diff_text = ""
    for file in files:
        if file.patch:
            diff_text += f"\nFile: {file.filename}\nPatch:\n{file.patch}\n"

    if not diff_text.strip():
        print("No code changes found in diff. Exiting.")
        return

    # Truncate large diffs for safety
    if len(diff_text) > MAX_DIFF_CHARS:
        print(f"Warning: Diff exceeds {MAX_DIFF_CHARS} chars. Truncating.")
        diff_text = diff_text[:MAX_DIFF_CHARS] + "\n...[Diff truncated due to size limits]..."

    review_data = process_pr_review(diff_text)
    if not review_data:
        pr.create_issue_comment("⚠️ **AI Code Review Failed:** Unable to process code diff structured output.")
        return

    # 1. Post General PR Summary
    formatted_body = format_github_comment(review_data)
    pr.create_issue_comment(formatted_body)

    # 2. Post Actual Inline Comments via GitHub Review API
    if review_data.inline_comments:
        comments_payload = []
        for ic in review_data.inline_comments:
            comments_payload.append({
                "path": ic.file_path,
                "line": ic.line_number,
                "body": ic.comment
            })
        
        try:
            # Submits a formal review with line-by-line inline annotations
            pr.create_review(
                body="**Inline Code Analysis & Fixes**",
                event="COMMENT",
                comments=comments_payload
            )
            print(f"Posted {len(comments_payload)} inline comments successfully!")
        except Exception as e:
            print(f"Warning: Could not post inline comments (line numbers might not match diff patch): {e}")

    print("Successfully completed AI review!")

def process_pr_review(diff_text: str) -> PRReviewResult | None:
    # Inject Pydantic schema directly into system prompt
    schema_json = json.dumps(PRReviewResult.model_json_schema(), indent=2)
    
    system_prompt = (
        "You are an expert Principal AI Engineer and Security Reviewer. "
        "Review the provided Git diff for code quality, security vulnerabilities, "
        "performance bottlenecks, and clean architecture.\n\n"
        "CRITICAL: You MUST respond strictly with valid JSON conforming to the following JSON Schema:\n"
        f"{schema_json}\n\n"
        "Do NOT include any preamble, conversational text, or markdown code blocks (like ```json). Output raw JSON only."
    )

    try:
        response = groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-specdec"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Review this PR diff:\n\n{diff_text}"}
            ],
            response_format={"type": "json_object"},  # Standard JSON mode supported across all Groq models
            temperature=0.2,
        )

        raw_json = response.choices[0].message.content
        cleaned_json = clean_json_response(raw_json)
        return PRReviewResult.model_validate_json(cleaned_json)

    except Exception as e:
        print(f"Error during AI model processing or schema validation: {e}")
        return None

def format_github_comment(review: PRReviewResult) -> str:
    issues_markdown = "\n".join([f"- {issue}" for issue in review.key_issues]) if review.key_issues else "- None identified."
    
    return f"""## AI Code Review Summary

**Overall Readiness Score:** `{review.overall_score}/10`

### Overview
{review.summary}

### Key Concerns & Security Issues
{issues_markdown}

---
*Generated automatically by `ai-pr-reviewer` powered by Llama 3.3 & Groq.*
"""

if __name__ == "__main__":
    run_review()