"""
Skill Loader - Load skills from filesystem (MD files, skill folders).
Supports loading skills from:
- Single .md files with YAML frontmatter
- Skill folders containing SKILL.md + templates, assets, references
"""

import os
import re
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class SkillParameter:
    """A parameter for a skill."""
    name: str
    type: str
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[str]] = None


@dataclass
class LoadedSkill:
    """A skill loaded from the filesystem."""
    id: str
    name: str
    description: str
    category: str
    parameters: List[SkillParameter]
    instructions: str
    integration_required: Optional[str] = None
    templates: Dict[str, str] = field(default_factory=dict)
    assets: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    source_path: str = ""
    is_builtin: bool = False


class SkillLoader:
    """Load skills from filesystem."""

    # Default skill directories to scan
    DEFAULT_SKILL_DIRS = [
        "~/.lazyagents/skills",
        "./skills",
        "./data/skills",
    ]

    def __init__(self, skill_dirs: Optional[List[str]] = None):
        self.skill_dirs = skill_dirs or self.DEFAULT_SKILL_DIRS
        self._skills_cache: Dict[str, LoadedSkill] = {}

    def load_all_skills(self) -> List[LoadedSkill]:
        """Load all skills from configured directories."""
        skills = []

        for skill_dir in self.skill_dirs:
            expanded_dir = Path(skill_dir).expanduser()
            if not expanded_dir.exists():
                continue

            # Scan for .md files (single-file skills)
            for md_file in expanded_dir.glob("*.md"):
                if md_file.name.lower() == "readme.md":
                    continue
                skill = self._load_md_skill(md_file)
                if skill:
                    skills.append(skill)
                    self._skills_cache[skill.id] = skill

            # Scan for skill folders (containing SKILL.md)
            for skill_folder in expanded_dir.iterdir():
                if skill_folder.is_dir():
                    skill_md = skill_folder / "SKILL.md"
                    if skill_md.exists():
                        skill = self._load_folder_skill(skill_folder)
                        if skill:
                            skills.append(skill)
                            self._skills_cache[skill.id] = skill

        return skills

    def load_skill_from_path(self, path: str) -> Optional[LoadedSkill]:
        """Load a skill from a specific path (file or folder)."""
        path_obj = Path(path).expanduser()

        if path_obj.is_file() and path_obj.suffix == ".md":
            return self._load_md_skill(path_obj)
        elif path_obj.is_dir():
            skill_md = path_obj / "SKILL.md"
            if skill_md.exists():
                return self._load_folder_skill(path_obj)

        return None

    def get_skill(self, skill_id: str) -> Optional[LoadedSkill]:
        """Get a skill by ID from cache."""
        return self._skills_cache.get(skill_id)

    def _load_md_skill(self, md_file: Path) -> Optional[LoadedSkill]:
        """Load a skill from a single .md file."""
        try:
            content = md_file.read_text(encoding="utf-8")
            frontmatter, body = self._parse_frontmatter(content)

            if not frontmatter:
                return None

            # Generate skill ID from filename
            skill_id = frontmatter.get("id", md_file.stem.lower().replace(" ", "_"))

            # Parse parameters from frontmatter
            params = []
            for param_data in frontmatter.get("parameters", []):
                params.append(SkillParameter(
                    name=param_data.get("name", ""),
                    type=param_data.get("type", "string"),
                    description=param_data.get("description", ""),
                    required=param_data.get("required", True),
                    default=param_data.get("default"),
                    enum=param_data.get("enum"),
                ))

            return LoadedSkill(
                id=skill_id,
                name=frontmatter.get("name", md_file.stem),
                description=frontmatter.get("description", ""),
                category=frontmatter.get("category", "custom"),
                parameters=params,
                instructions=body,
                integration_required=frontmatter.get("integration"),
                source_path=str(md_file),
                is_builtin=False,
            )
        except Exception as e:
            print(f"Error loading skill from {md_file}: {e}")
            return None

    def _load_folder_skill(self, skill_folder: Path) -> Optional[LoadedSkill]:
        """Load a skill from a folder containing SKILL.md."""
        skill_md = skill_folder / "SKILL.md"

        try:
            content = skill_md.read_text(encoding="utf-8")
            frontmatter, body = self._parse_frontmatter(content)

            if not frontmatter:
                return None

            # Generate skill ID from folder name
            skill_id = frontmatter.get("id", skill_folder.name.lower().replace(" ", "_"))

            # Parse parameters
            params = []
            for param_data in frontmatter.get("parameters", []):
                params.append(SkillParameter(
                    name=param_data.get("name", ""),
                    type=param_data.get("type", "string"),
                    description=param_data.get("description", ""),
                    required=param_data.get("required", True),
                    default=param_data.get("default"),
                    enum=param_data.get("enum"),
                ))

            # Load templates
            templates = {}
            templates_dir = skill_folder / "templates"
            if templates_dir.exists():
                for template_file in templates_dir.glob("*"):
                    if template_file.is_file():
                        templates[template_file.name] = template_file.read_text(encoding="utf-8")

            # Collect assets
            assets = []
            assets_dir = skill_folder / "assets"
            if assets_dir.exists():
                for asset_file in assets_dir.glob("*"):
                    if asset_file.is_file():
                        assets.append(str(asset_file))

            # Collect references
            references = []
            refs_dir = skill_folder / "references"
            if refs_dir.exists():
                for ref_file in refs_dir.glob("*.md"):
                    references.append(ref_file.read_text(encoding="utf-8"))

            return LoadedSkill(
                id=skill_id,
                name=frontmatter.get("name", skill_folder.name),
                description=frontmatter.get("description", ""),
                category=frontmatter.get("category", "custom"),
                parameters=params,
                instructions=body,
                integration_required=frontmatter.get("integration"),
                templates=templates,
                assets=assets,
                references=references,
                source_path=str(skill_folder),
                is_builtin=False,
            )
        except Exception as e:
            print(f"Error loading skill from {skill_folder}: {e}")
            return None

    def _parse_frontmatter(self, content: str) -> tuple[Optional[Dict[str, Any]], str]:
        """Parse YAML frontmatter from markdown content."""
        # Match YAML frontmatter between ---
        frontmatter_pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
        match = re.match(frontmatter_pattern, content, re.DOTALL)

        if not match:
            return None, content

        try:
            frontmatter = yaml.safe_load(match.group(1))
            body = match.group(2)
            return frontmatter, body
        except yaml.YAMLError:
            return None, content

    def to_db_format(self, skill: LoadedSkill) -> Dict[str, Any]:
        """Convert a loaded skill to database format."""
        parameters = {}
        for param in skill.parameters:
            param_def = {
                "type": param.type,
                "description": param.description,
            }
            if param.default is not None:
                param_def["default"] = param.default
            if param.enum:
                param_def["enum"] = param.enum
            parameters[param.name] = param_def

        return {
            "id": skill.id,
            "name": skill.name,
            "description": skill.description,
            "category": skill.category,
            "parameters": parameters,
            "integration_required": skill.integration_required,
            "is_builtin": skill.is_builtin,
            "implementation_type": "prompt",
            "implementation": json.dumps({
                "instructions": skill.instructions,
                "templates": skill.templates,
                "references": skill.references,
            }),
            "source_path": skill.source_path,
        }


# Example skill markdown format:
EXAMPLE_SKILL_MD = '''---
name: Summarize Repository
description: Analyze a GitHub repository and create a summary of its purpose and structure
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

```
# Repository Summary: owner/repo

## Overview
This is a web application for managing tasks...

## Tech Stack
- Python 3.11
- FastAPI
- PostgreSQL
...
```
'''
