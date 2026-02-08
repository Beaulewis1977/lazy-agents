"""
Skill Executor - Execute skills by calling real APIs.
Implements actual integrations for GitHub, Discord, Slack, HTTP, File, etc.
"""

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar

import httpx


@dataclass
class SkillResult:
    """Result from executing a skill."""

    success: bool
    data: Any
    error: str | None = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class BaseSkillExecutor(ABC):
    """Base class for skill executors."""

    @abstractmethod
    async def execute(
        self, skill_id: str, params: dict[str, Any], credentials: dict[str, str]
    ) -> SkillResult:
        """Execute a skill with given parameters."""
        pass


class GitHubSkillExecutor(BaseSkillExecutor):
    """Execute GitHub-related skills."""

    BASE_URL = "https://api.github.com"

    async def execute(
        self, skill_id: str, params: dict[str, Any], credentials: dict[str, str]
    ) -> SkillResult:
        token = credentials.get("token")
        if not token:
            return SkillResult(success=False, data=None, error="GitHub token not configured")

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if skill_id == "github.list_issues":
                    return await self._list_issues(client, headers, params)
                elif skill_id == "github.create_issue":
                    return await self._create_issue(client, headers, params)
                elif skill_id == "github.get_repo":
                    return await self._get_repo(client, headers, params)
                elif skill_id == "github.list_prs":
                    return await self._list_prs(client, headers, params)
                elif skill_id == "github.get_file":
                    return await self._get_file(client, headers, params)
                elif skill_id == "github.list_commits":
                    return await self._list_commits(client, headers, params)
                else:
                    return SkillResult(
                        success=False, data=None, error=f"Unknown GitHub skill: {skill_id}"
                    )
            except httpx.HTTPStatusError as e:
                return SkillResult(
                    success=False,
                    data=None,
                    error=f"GitHub API error: {e.response.status_code} - {e.response.text}",
                )
            except Exception as e:
                return SkillResult(success=False, data=None, error=str(e))

    async def _list_issues(
        self, client: httpx.AsyncClient, headers: dict, params: dict
    ) -> SkillResult:
        repo = params.get("repo", "")
        state = params.get("state", "open")
        limit = params.get("limit", 10)

        response = await client.get(
            f"{self.BASE_URL}/repos/{repo}/issues",
            headers=headers,
            params={"state": state, "per_page": limit},
        )
        response.raise_for_status()
        issues = response.json()

        return SkillResult(
            success=True,
            data=[
                {
                    "number": i["number"],
                    "title": i["title"],
                    "state": i["state"],
                    "author": i["user"]["login"],
                    "created_at": i["created_at"],
                    "labels": [label["name"] for label in i.get("labels", [])],
                    "url": i["html_url"],
                }
                for i in issues
            ],
            metadata={"total": len(issues)},
        )

    async def _create_issue(
        self, client: httpx.AsyncClient, headers: dict, params: dict
    ) -> SkillResult:
        repo = params.get("repo", "")
        title = params.get("title", "")
        body = params.get("body", "")
        labels = params.get("labels", [])

        response = await client.post(
            f"{self.BASE_URL}/repos/{repo}/issues",
            headers=headers,
            json={"title": title, "body": body, "labels": labels},
        )
        response.raise_for_status()
        issue = response.json()

        return SkillResult(
            success=True,
            data={
                "number": issue["number"],
                "title": issue["title"],
                "url": issue["html_url"],
            },
        )

    async def _get_repo(
        self, client: httpx.AsyncClient, headers: dict, params: dict
    ) -> SkillResult:
        repo = params.get("repo", "")

        response = await client.get(f"{self.BASE_URL}/repos/{repo}", headers=headers)
        response.raise_for_status()
        data = response.json()

        return SkillResult(
            success=True,
            data={
                "name": data["name"],
                "full_name": data["full_name"],
                "description": data["description"],
                "language": data["language"],
                "stars": data["stargazers_count"],
                "forks": data["forks_count"],
                "open_issues": data["open_issues_count"],
                "default_branch": data["default_branch"],
                "url": data["html_url"],
            },
        )

    async def _list_prs(
        self, client: httpx.AsyncClient, headers: dict, params: dict
    ) -> SkillResult:
        repo = params.get("repo", "")
        state = params.get("state", "open")
        limit = params.get("limit", 10)

        response = await client.get(
            f"{self.BASE_URL}/repos/{repo}/pulls",
            headers=headers,
            params={"state": state, "per_page": limit},
        )
        response.raise_for_status()
        prs = response.json()

        return SkillResult(
            success=True,
            data=[
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "state": pr["state"],
                    "author": pr["user"]["login"],
                    "created_at": pr["created_at"],
                    "url": pr["html_url"],
                }
                for pr in prs
            ],
        )

    async def _get_file(
        self, client: httpx.AsyncClient, headers: dict, params: dict
    ) -> SkillResult:
        repo = params.get("repo", "")
        path = params.get("path", "README.md")

        response = await client.get(
            f"{self.BASE_URL}/repos/{repo}/contents/{path}",
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        import base64

        content = base64.b64decode(data["content"]).decode("utf-8")

        return SkillResult(
            success=True,
            data={"path": path, "content": content, "size": data["size"]},
        )

    async def _list_commits(
        self, client: httpx.AsyncClient, headers: dict, params: dict
    ) -> SkillResult:
        repo = params.get("repo", "")
        limit = params.get("limit", 10)

        response = await client.get(
            f"{self.BASE_URL}/repos/{repo}/commits",
            headers=headers,
            params={"per_page": limit},
        )
        response.raise_for_status()
        commits = response.json()

        return SkillResult(
            success=True,
            data=[
                {
                    "sha": c["sha"][:7],
                    "message": c["commit"]["message"].split("\n")[0],
                    "author": c["commit"]["author"]["name"],
                    "date": c["commit"]["author"]["date"],
                }
                for c in commits
            ],
        )


class DiscordSkillExecutor(BaseSkillExecutor):
    """Execute Discord-related skills."""

    BASE_URL = "https://discord.com/api/v10"

    async def execute(
        self, skill_id: str, params: dict[str, Any], credentials: dict[str, str]
    ) -> SkillResult:
        token = credentials.get("bot_token")
        if not token:
            return SkillResult(success=False, data=None, error="Discord bot token not configured")

        headers = {
            "Authorization": f"Bot {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if skill_id == "discord.send_message":
                    return await self._send_message(client, headers, params)
                elif skill_id == "discord.get_messages":
                    return await self._get_messages(client, headers, params)
                else:
                    return SkillResult(
                        success=False, data=None, error=f"Unknown Discord skill: {skill_id}"
                    )
            except httpx.HTTPStatusError as e:
                return SkillResult(
                    success=False, data=None, error=f"Discord API error: {e.response.status_code}"
                )
            except Exception as e:
                return SkillResult(success=False, data=None, error=str(e))

    async def _send_message(
        self, client: httpx.AsyncClient, headers: dict, params: dict
    ) -> SkillResult:
        channel_id = params.get("channel_id", "")
        content = params.get("content", "")

        response = await client.post(
            f"{self.BASE_URL}/channels/{channel_id}/messages",
            headers=headers,
            json={"content": content},
        )
        response.raise_for_status()
        msg = response.json()

        return SkillResult(
            success=True,
            data={"message_id": msg["id"], "channel_id": channel_id},
        )

    async def _get_messages(
        self, client: httpx.AsyncClient, headers: dict, params: dict
    ) -> SkillResult:
        channel_id = params.get("channel_id", "")
        limit = params.get("limit", 10)

        response = await client.get(
            f"{self.BASE_URL}/channels/{channel_id}/messages",
            headers=headers,
            params={"limit": limit},
        )
        response.raise_for_status()
        messages = response.json()

        return SkillResult(
            success=True,
            data=[
                {
                    "id": m["id"],
                    "content": m["content"],
                    "author": m["author"]["username"],
                    "timestamp": m["timestamp"],
                }
                for m in messages
            ],
        )


class SlackSkillExecutor(BaseSkillExecutor):
    """Execute Slack-related skills."""

    BASE_URL = "https://slack.com/api"

    async def execute(
        self, skill_id: str, params: dict[str, Any], credentials: dict[str, str]
    ) -> SkillResult:
        token = credentials.get("bot_token")
        if not token:
            return SkillResult(success=False, data=None, error="Slack bot token not configured")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                if skill_id == "slack.send_message":
                    return await self._send_message(client, headers, params)
                elif skill_id == "slack.get_messages":
                    return await self._get_messages(client, headers, params)
                else:
                    return SkillResult(
                        success=False, data=None, error=f"Unknown Slack skill: {skill_id}"
                    )
            except Exception as e:
                return SkillResult(success=False, data=None, error=str(e))

    async def _send_message(
        self, client: httpx.AsyncClient, headers: dict, params: dict
    ) -> SkillResult:
        channel = params.get("channel", "")
        text = params.get("text", "")

        response = await client.post(
            f"{self.BASE_URL}/chat.postMessage",
            headers=headers,
            json={"channel": channel, "text": text},
        )
        data = response.json()

        if not data.get("ok"):
            return SkillResult(success=False, data=None, error=data.get("error", "Unknown error"))

        return SkillResult(
            success=True,
            data={"ts": data["ts"], "channel": data["channel"]},
        )

    async def _get_messages(
        self, client: httpx.AsyncClient, headers: dict, params: dict
    ) -> SkillResult:
        channel = params.get("channel", "")
        limit = params.get("limit", 10)

        response = await client.get(
            f"{self.BASE_URL}/conversations.history",
            headers=headers,
            params={"channel": channel, "limit": limit},
        )
        data = response.json()

        if not data.get("ok"):
            return SkillResult(success=False, data=None, error=data.get("error", "Unknown error"))

        return SkillResult(
            success=True,
            data=[
                {
                    "text": m["text"],
                    "user": m.get("user", "bot"),
                    "ts": m["ts"],
                }
                for m in data.get("messages", [])
            ],
        )


class HTTPSkillExecutor(BaseSkillExecutor):
    """Execute generic HTTP requests."""

    async def execute(
        self, skill_id: str, params: dict[str, Any], credentials: dict[str, str]
    ) -> SkillResult:
        url = params.get("url", "")
        method = params.get("method", "GET").upper()
        headers = params.get("headers", {})
        body = params.get("body")
        timeout = params.get("timeout", 30)

        async with httpx.AsyncClient() as client:
            try:
                if method == "GET":
                    response = await client.get(url, headers=headers, timeout=timeout)
                elif method == "POST":
                    response = await client.post(url, headers=headers, json=body, timeout=timeout)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, json=body, timeout=timeout)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers, timeout=timeout)
                elif method == "PATCH":
                    response = await client.patch(url, headers=headers, json=body, timeout=timeout)
                else:
                    return SkillResult(
                        success=False, data=None, error=f"Unsupported HTTP method: {method}"
                    )

                # Try to parse as JSON
                try:
                    data = response.json()
                except (ValueError, TypeError):
                    data = response.text

                return SkillResult(
                    success=response.is_success,
                    data=data,
                    metadata={
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                    },
                )
            except Exception as e:
                return SkillResult(success=False, data=None, error=str(e))


class FileSkillExecutor(BaseSkillExecutor):
    """Execute file system operations."""

    def __init__(self, allowed_paths: list[str] | None = None):
        self.allowed_paths = allowed_paths or []

    def _is_path_allowed(self, path: str) -> bool:
        """Check if path is within allowed directories."""
        if not self.allowed_paths:
            return True  # Allow all if no restrictions

        abs_path = os.path.abspath(path)
        return any(abs_path.startswith(os.path.abspath(allowed)) for allowed in self.allowed_paths)

    async def execute(
        self, skill_id: str, params: dict[str, Any], credentials: dict[str, str]
    ) -> SkillResult:
        try:
            if skill_id == "file.read":
                return await self._read_file(params)
            elif skill_id == "file.write":
                return await self._write_file(params)
            elif skill_id == "file.list":
                return await self._list_files(params)
            elif skill_id == "file.exists":
                return await self._file_exists(params)
            else:
                return SkillResult(
                    success=False, data=None, error=f"Unknown file skill: {skill_id}"
                )
        except Exception as e:
            return SkillResult(success=False, data=None, error=str(e))

    async def _read_file(self, params: dict) -> SkillResult:
        path = params.get("path", "")

        if not self._is_path_allowed(path):
            return SkillResult(success=False, data=None, error="Path not allowed")

        if not os.path.exists(path):
            return SkillResult(success=False, data=None, error=f"File not found: {path}")

        with open(path, encoding="utf-8") as f:
            content = f.read()

        return SkillResult(success=True, data={"path": path, "content": content})

    async def _write_file(self, params: dict) -> SkillResult:
        path = params.get("path", "")
        content = params.get("content", "")

        if not self._is_path_allowed(path):
            return SkillResult(success=False, data=None, error="Path not allowed")

        # Create directory if needed
        os.makedirs(os.path.dirname(path), exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return SkillResult(success=True, data={"path": path, "bytes_written": len(content)})

    async def _list_files(self, params: dict) -> SkillResult:
        path = params.get("path", ".")
        pattern = params.get("pattern", "*")

        if not self._is_path_allowed(path):
            return SkillResult(success=False, data=None, error="Path not allowed")

        from pathlib import Path

        files = list(Path(path).glob(pattern))

        return SkillResult(
            success=True,
            data=[
                {
                    "name": f.name,
                    "path": str(f),
                    "is_dir": f.is_dir(),
                    "size": f.stat().st_size if f.is_file() else None,
                }
                for f in files[:100]
            ],  # Limit to 100 files
        )

    async def _file_exists(self, params: dict) -> SkillResult:
        path = params.get("path", "")
        exists = os.path.exists(path)
        return SkillResult(success=True, data={"exists": exists, "path": path})


class ShellSkillExecutor(BaseSkillExecutor):
    """Execute shell commands (with safety restrictions)."""

    ALLOWED_COMMANDS: ClassVar[list[str]] = [
        "ls",
        "cat",
        "head",
        "tail",
        "grep",
        "wc",
        "find",
        "echo",
        "pwd",
        "date",
    ]

    async def execute(
        self, skill_id: str, params: dict[str, Any], credentials: dict[str, str]
    ) -> SkillResult:
        import asyncio

        command = params.get("command", "")
        timeout = params.get("timeout", 30)

        # Basic safety check
        first_word = command.split()[0] if command else ""
        if first_word not in self.ALLOWED_COMMANDS:
            return SkillResult(
                success=False,
                data=None,
                error=f"Command '{first_word}' not allowed. Allowed: {', '.join(self.ALLOWED_COMMANDS)}",
            )

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

            return SkillResult(
                success=proc.returncode == 0,
                data={
                    "stdout": stdout.decode("utf-8").strip(),
                    "stderr": stderr.decode("utf-8").strip(),
                    "return_code": proc.returncode,
                },
            )
        except TimeoutError:
            return SkillResult(success=False, data=None, error="Command timed out")
        except Exception as e:
            return SkillResult(success=False, data=None, error=str(e))


class SkillExecutorRegistry:
    """Registry of skill executors."""

    def __init__(self):
        self.executors: dict[str, BaseSkillExecutor] = {
            "github": GitHubSkillExecutor(),
            "discord": DiscordSkillExecutor(),
            "slack": SlackSkillExecutor(),
            "http": HTTPSkillExecutor(),
            "file": FileSkillExecutor(),
            "shell": ShellSkillExecutor(),
        }

    def get_executor(self, skill_id: str) -> BaseSkillExecutor | None:
        """Get executor for a skill based on its ID prefix."""
        prefix = skill_id.split(".")[0]
        return self.executors.get(prefix)

    async def execute_skill(
        self,
        skill_id: str,
        params: dict[str, Any],
        credentials: dict[str, str] | None = None,
    ) -> SkillResult:
        """Execute a skill by ID."""
        executor = self.get_executor(skill_id)

        if not executor:
            return SkillResult(
                success=False,
                data=None,
                error=f"No executor found for skill: {skill_id}",
            )

        return await executor.execute(skill_id, params, credentials or {})


# Global registry
skill_executor_registry = SkillExecutorRegistry()
