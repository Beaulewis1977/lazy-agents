import json
import logging
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decrypt_secret, redact_sensitive_data, redact_sensitive_string
from app.models.agent import Agent
from app.models.execution import Execution, ExecutionStep
from app.models.integration import Integration
from app.models.skill import Skill
from app.runtime.llm_client import LLMMessage, LLMResponse, get_llm_client
from app.runtime.skill_executor import SkillResult, skill_executor_registry

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for an agent execution."""

    execution_id: str
    agent: Agent
    skills: list[Skill]
    integrations: dict[str, Integration]  # type -> integration
    input_data: dict[str, Any]
    memory: list[dict[str, Any]] = field(default_factory=list)
    logs: list[str] = field(default_factory=list)

    def log(self, message: str):
        timestamp = datetime.utcnow().isoformat()
        self.logs.append(f"[{timestamp}] {message}")


class AgentExecutor:
    """Execute an agent with LLM and skill calling."""

    MAX_ITERATIONS = 10  # Maximum tool-calling iterations

    def __init__(self, db: AsyncSession):
        self.db = db
        self._log_callbacks: list[Callable[[dict[str, Any]], Awaitable[None]]] = []

    def add_log_callback(self, callback: Callable[[dict[str, Any]], Awaitable[None]]):
        """Add a callback for real-time log streaming."""
        self._log_callbacks.append(callback)

    async def _emit_log(self, execution_id: str, level: str, message: str, source: str = "agent"):
        """Emit a log message to all callbacks."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "execution_id": execution_id,
            "level": level,
            "message": redact_sensitive_string(message),
            "source": source,
        }
        for callback in self._log_callbacks:
            try:
                await callback(log_entry)
            except Exception:
                logger.debug("Log callback failed", exc_info=True)

    async def execute(
        self,
        agent_id: str,
        input_data: dict[str, Any] | None = None,
        trigger: str = "manual",
        api_keys: dict[str, str] | None = None,
    ) -> Execution:
        """Execute an agent and return the execution record."""
        input_payload = input_data or {}
        redacted_input_payload = redact_sensitive_data(input_payload)

        # Load agent
        result = await self.db.execute(select(Agent).where(Agent.id == agent_id))
        agent = result.scalar_one_or_none()

        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Create execution record
        execution = Execution(
            id=str(uuid.uuid4()),
            agent_id=agent_id,
            trigger=trigger,
            status="running",
            started_at=datetime.utcnow(),
            input_data=redacted_input_payload,
        )
        self.db.add(execution)
        await self.db.commit()

        await self._emit_log(
            execution.id, "info", f"Starting execution of agent: {agent.name}", "system"
        )

        try:
            # Load agent's skills
            skills = await self._load_skills(agent.skills or [])

            # Load agent's integrations with credentials
            integrations = await self._load_integrations(agent.integrations or [])

            # Create execution context
            context = ExecutionContext(
                execution_id=execution.id,
                agent=agent,
                skills=skills,
                integrations=integrations,
                input_data=input_payload,
            )

            # Run the agent loop
            result = await self._run_agent_loop(context, api_keys or {})

            # Update execution record
            execution.status = "success"
            execution.completed_at = datetime.utcnow()
            execution.output_data = redact_sensitive_data(result)
            execution.tokens_input = (
                context.memory[-1].get("tokens_input", 0) if context.memory else 0
            )
            execution.tokens_output = (
                context.memory[-1].get("tokens_output", 0) if context.memory else 0
            )

            await self._emit_log(execution.id, "info", "Execution completed successfully", "system")

        except Exception as e:
            execution.status = "failed"
            execution.completed_at = datetime.utcnow()
            execution.error_message = redact_sensitive_string(str(e))

            await self._emit_log(execution.id, "error", f"Execution failed: {e!s}", "system")

        # Update agent stats
        agent.last_run_at = datetime.utcnow()
        agent.total_runs = (agent.total_runs or 0) + 1
        if execution.status == "success":
            agent.successful_runs = (agent.successful_runs or 0) + 1

        await self.db.commit()
        await self.db.refresh(execution)

        return execution

    async def _load_skills(self, skill_ids: list[str]) -> list[Skill]:
        """Load skills by ID."""
        if not skill_ids:
            return []

        result = await self.db.execute(select(Skill).where(Skill.id.in_(skill_ids)))
        return list(result.scalars().all())

    async def _load_integrations(self, integration_ids: list[str]) -> dict[str, Integration]:
        """Load integrations by ID, mapped by type."""
        if not integration_ids:
            return {}

        result = await self.db.execute(
            select(Integration).where(Integration.id.in_(integration_ids))
        )
        integrations = {}
        for integration in result.scalars().all():
            integrations[integration.type] = integration
        return integrations

    def _get_integration_credentials(self, integration: Integration) -> dict[str, str]:
        """Decrypt credentials from an integration."""
        if not integration.credentials_encrypted:
            return {}
        try:
            decrypted = decrypt_secret(integration.credentials_encrypted)
            return json.loads(decrypted)
        except Exception:
            return {}

    async def _run_agent_loop(
        self,
        context: ExecutionContext,
        api_keys: dict[str, str],
    ) -> dict[str, Any]:
        """Run the main agent loop with tool calling."""

        agent = context.agent

        # Get the appropriate LLM client
        # Check for API key override from request, then from integration, then from env (via client defaults)
        model = agent.model or "gpt-4o-mini"
        api_key = None

        if model.startswith("gpt-") or model.startswith("o1") or model.startswith("o3"):
            api_key = api_keys.get("openai")
            if not api_key and "openai" in context.integrations:
                creds = self._get_integration_credentials(context.integrations["openai"])
                api_key = creds.get("api_key")
        elif model.startswith("claude-"):
            api_key = api_keys.get("anthropic")
            if not api_key and "anthropic" in context.integrations:
                creds = self._get_integration_credentials(context.integrations["anthropic"])
                api_key = creds.get("api_key")
        elif model.startswith("gemini-"):
            api_key = api_keys.get("google")
            if not api_key and "google" in context.integrations:
                creds = self._get_integration_credentials(context.integrations["google"])
                api_key = creds.get("api_key")

        # Fallback for old "o1" or similar if needed
        if (
            not api_key
            and "openai" in context.integrations
            and not model.startswith("claude-")
            and not model.startswith("gemini-")
        ):
            creds = self._get_integration_credentials(context.integrations["openai"])
            api_key = creds.get("api_key")

        llm = get_llm_client(model, api_key)

        # Build the system prompt
        system_prompt = self._build_system_prompt(context)

        # Build tool definitions from skills
        tools = self._build_tool_definitions(context.skills)

        # Initialize conversation
        messages = [
            LLMMessage(role="system", content=system_prompt),
        ]

        # Add user input
        user_message = self._format_user_input(context.input_data)
        messages.append(LLMMessage(role="user", content=user_message))

        await self._emit_log(
            context.execution_id, "info", f"User input: {user_message[:200]}...", "agent"
        )

        # Run the loop
        total_tokens_input = 0
        total_tokens_output = 0
        iteration = 0
        final_response = ""

        while iteration < self.MAX_ITERATIONS:
            iteration += 1

            await self._emit_log(context.execution_id, "debug", f"Iteration {iteration}", "agent")

            try:
                # Call LLM
                response = await llm.chat(
                    messages=messages,
                    model=model,
                    temperature=agent.temperature or 0.7,
                    tools=tools if tools else None,
                )

                total_tokens_input += response.tokens_input
                total_tokens_output += response.tokens_output

                # Check for tool calls
                tool_calls = self._extract_tool_calls(response)

                if not tool_calls:
                    # No more tool calls, we're done
                    final_response = response.content
                    await self._emit_log(
                        context.execution_id, "info", "Final response generated", "agent"
                    )
                    break

                # Execute tool calls
                messages.append(LLMMessage(role="assistant", content=response.content or ""))

                for tool_call in tool_calls:
                    tool_name = tool_call["name"]
                    tool_args = tool_call["arguments"]

                    await self._emit_log(
                        context.execution_id, "info", f"Calling skill: {tool_name}", "skill"
                    )

                    # Execute the skill
                    skill_result = await self._execute_skill(context, tool_name, tool_args)

                    # Record step
                    step = ExecutionStep(
                        id=str(uuid.uuid4()),
                        execution_id=context.execution_id,
                        step_number=iteration,
                        step_type="tool_call",
                        name=tool_name,
                        status="success" if skill_result.success else "failed",
                        started_at=datetime.utcnow(),
                        completed_at=datetime.utcnow(),
                        input_data=redact_sensitive_data(tool_args),
                        output_data=redact_sensitive_data({"result": skill_result.data})
                        if skill_result.success
                        else None,
                        error_message=redact_sensitive_string(skill_result.error)
                        if skill_result.error
                        else None,
                    )
                    self.db.add(step)

                    # Add tool response to conversation
                    tool_response = (
                        json.dumps(skill_result.data)
                        if skill_result.success
                        else f"Error: {skill_result.error}"
                    )
                    messages.append(
                        LLMMessage(
                            role="user", content=f"Tool '{tool_name}' result:\n{tool_response}"
                        )
                    )

                    await self._emit_log(
                        context.execution_id,
                        "info" if skill_result.success else "warn",
                        f"Skill {tool_name} {'completed' if skill_result.success else 'failed'}",
                        "skill",
                    )
            except Exception as e:
                await self._emit_log(
                    context.execution_id, "error", f"Error in loop: {e!s}", "agent"
                )
                raise

        # Store execution metadata
        context.memory.append(
            {
                "tokens_input": total_tokens_input,
                "tokens_output": total_tokens_output,
                "iterations": iteration,
            }
        )

        return {
            "response": final_response,
            "tokens_input": total_tokens_input,
            "tokens_output": total_tokens_output,
            "iterations": iteration,
        }

    def _build_system_prompt(self, context: ExecutionContext) -> str:
        """Build the system prompt for the agent."""
        agent = context.agent

        prompt_parts = []

        # Base system prompt
        if agent.system_prompt:
            prompt_parts.append(agent.system_prompt)
        else:
            prompt_parts.append(f"You are {agent.name}, an AI assistant.")
            if agent.description:
                prompt_parts.append(f"Your purpose: {agent.description}")

        # Add skill information
        if context.skills:
            skills_info = "\n\nYou have access to the following skills (tools):\n"
            for skill in context.skills:
                skills_info += f"\n- {skill.name} ({skill.id}): {skill.description}"
            prompt_parts.append(skills_info)

        # Add integration context
        if context.integrations:
            integrations_info = "\n\nYou are connected to the following services:\n"
            for int_type, integration in context.integrations.items():
                integrations_info += f"\n- {integration.name} ({int_type})"
            prompt_parts.append(integrations_info)

        return "\n".join(prompt_parts)

    def _build_tool_definitions(self, skills: list[Skill]) -> list[dict[str, Any]]:
        """Build OpenAI-style tool definitions from skills."""
        tools = []

        for skill in skills:
            # Convert parameters to JSON Schema
            properties = {}
            required = []

            for param_name, param_info in (skill.parameters or {}).items():
                prop = {
                    "type": param_info.get("type", "string"),
                    "description": param_info.get("description", ""),
                }
                if "enum" in param_info:
                    prop["enum"] = param_info["enum"]
                if "default" in param_info:
                    prop["default"] = param_info["default"]
                else:
                    required.append(param_name)

                properties[param_name] = prop

            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": skill.id,
                        "description": skill.description or skill.name,
                        "parameters": {
                            "type": "object",
                            "properties": properties,
                            "required": required,
                        },
                    },
                }
            )

        return tools

    def _format_user_input(self, input_data: dict[str, Any]) -> str:
        """Format user input for the conversation."""
        if not input_data:
            return "Please proceed with your task."

        if "message" in input_data:
            return input_data["message"]

        if "prompt" in input_data:
            return input_data["prompt"]

        return json.dumps(input_data, indent=2)

    def _extract_tool_calls(self, response: LLMResponse) -> list[dict[str, Any]]:
        """Extract tool calls from LLM response."""
        raw = response.raw_response

        # OpenAI format
        if raw.get("choices"):
            choice = raw["choices"][0]
            message = choice.get("message", {})
            tool_calls = message.get("tool_calls", [])

            if tool_calls:
                parsed_tool_calls = []
                for tc in tool_calls:
                    function_data = tc.get("function", {})
                    raw_arguments = function_data.get("arguments", "{}")
                    parsed_arguments: dict[str, Any]
                    try:
                        decoded_arguments = (
                            json.loads(raw_arguments)
                            if isinstance(raw_arguments, str)
                            else raw_arguments
                        )
                        if isinstance(decoded_arguments, dict):
                            parsed_arguments = decoded_arguments
                        else:
                            parsed_arguments = {"value": decoded_arguments}
                    except json.JSONDecodeError:
                        logger.warning(
                            "Malformed tool call arguments JSON",
                            extra={
                                "tool_call_id": tc.get("id", ""),
                                "tool_name": function_data.get("name", ""),
                            },
                        )
                        parsed_arguments = {"raw": str(raw_arguments)}
                    except Exception:
                        logger.exception("Unexpected error while parsing tool call arguments")
                        parsed_arguments = {}

                    parsed_tool_calls.append(
                        {
                            "id": tc.get("id", ""),
                            "name": function_data.get("name", ""),
                            "arguments": parsed_arguments,
                        }
                    )
                return parsed_tool_calls

        # Anthropic format
        if "content" in raw and isinstance(raw["content"], list):
            tool_calls = []
            for block in raw.get("content", []):
                if block.get("type") == "tool_use":
                    tool_calls.append(
                        {
                            "id": block.get("id", ""),
                            "name": block["name"],
                            "arguments": block["input"],
                        }
                    )
            return tool_calls

        return []

    async def _execute_skill(
        self,
        context: ExecutionContext,
        skill_id: str,
        params: dict[str, Any],
    ) -> SkillResult:
        """Execute a skill with the given parameters."""

        # Get credentials from integrations
        prefix = skill_id.split(".")[0]
        # Map skill prefix to integration type
        # Ideally skill definition should specify integration type, but for now infer from prefix
        # Except for custom.* skills, where we might need to look up which integration they use

        # Try to find matching integration
        integration = None
        if prefix in context.integrations:
            integration = context.integrations[prefix]
        else:
            # Look for skill in context to see if it has 'integration' field (mapped to category in some places?)
            # In Skill model we don't have explicit 'integration' field, but we have 'integration_required' string
            # Find the skill object
            skill = next((s for s in context.skills if s.id == skill_id), None)
            if skill and skill.integration_required:
                integration = context.integrations.get(skill.integration_required)

        credentials = self._get_integration_credentials(integration) if integration else {}

        # Execute via skill registry
        return await skill_executor_registry.execute_skill(skill_id, params, credentials)
