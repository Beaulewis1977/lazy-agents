---
name: Summarize Repository
description: Analyze a GitHub repository and create a summary of its purpose and structure
id: custom.summarize_repo
category: github
integration: github
parameters:
  - name: repo
    type: string
    description: Repository in owner/repo format
    required: true
  - name: depth
    type: string
    enum: [shallow, deep]
    default: shallow
    description: How detailed the analysis should be
---

# Summarize Repository Skill

This skill analyzes a GitHub repository and creates a comprehensive summary.

## Instructions

1. First, fetch the repository metadata using the GitHub API
2. Read the README.md file if it exists
3. Analyze the directory structure
4. Identify the main programming languages used
5. Look for key configuration files (package.json, requirements.txt, etc.)

## Output Format

Provide a summary with the following sections:
- **Overview**: Brief description of what the project does
- **Tech Stack**: Languages and frameworks used
- **Structure**: Key directories and their purposes
- **Getting Started**: How to run/use the project

## Example Output

```markdown
# Repository Summary: owner/repo

## Overview
This is a web application for managing tasks...

## Tech Stack
- Python 3.11
- FastAPI
- PostgreSQL

## Structure
- `/src` - Main source code
- `/tests` - Test files
- `/docs` - Documentation
```
