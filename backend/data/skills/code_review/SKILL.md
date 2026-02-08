---
name: Automated Code Review
description: Review code changes and provide actionable feedback
id: custom.code_review
category: development
integration: github
parameters:
  - name: pr_url
    type: string
    description: URL of the pull request to review
    required: true
  - name: focus_areas
    type: array
    description: Areas to focus on during review
    default: ["security", "performance", "readability"]
  - name: severity_threshold
    type: string
    enum: [low, medium, high]
    default: medium
    description: Minimum severity level to report
---

# Automated Code Review

This skill performs an automated code review on a pull request and provides structured feedback.

## Review Process

1. Fetch the diff from the pull request
2. Analyze changes file by file
3. Check against configured focus areas
4. Generate feedback with specific line references
5. Post comments on the PR or return structured feedback

## Focus Areas

### Security
- SQL injection vulnerabilities
- XSS potential
- Hardcoded credentials
- Insecure dependencies

### Performance
- N+1 queries
- Unnecessary loops
- Memory leaks
- Missing caching

### Readability
- Naming conventions
- Code complexity
- Missing documentation
- Test coverage

## Using Templates

This skill includes templates for different types of feedback to ensure consistent messaging.
