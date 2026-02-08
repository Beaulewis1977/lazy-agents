"""
Scheduler - Schedule and execute agents on a cron-like schedule.
Uses APScheduler for background job scheduling.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional, Callable
from croniter import croniter

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore

logger = logging.getLogger(__name__)


class AgentScheduler:
    """
    Scheduler for running agents on a schedule.
    Supports cron expressions for flexible scheduling.
    """

    def __init__(self):
        self.scheduler = AsyncIOScheduler(
            jobstores={"default": MemoryJobStore()},
            job_defaults={
                "coalesce": True,
                "max_instances": 1,
                "misfire_grace_time": 60,
            },
        )
        self._execute_callback: Optional[Callable] = None
        self._is_running = False

    def set_execute_callback(self, callback: Callable):
        """
        Set the callback function that will be called when an agent should run.
        The callback should accept (agent_id: str, trigger: str) as arguments.
        """
        self._execute_callback = callback

    def start(self):
        """Start the scheduler."""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            logger.info("Agent scheduler started")

    def stop(self):
        """Stop the scheduler."""
        if self._is_running:
            self.scheduler.shutdown(wait=False)
            self._is_running = False
            logger.info("Agent scheduler stopped")

    def schedule_agent(self, agent_id: str, cron_expression: str) -> bool:
        """
        Schedule an agent to run on a cron schedule.

        Args:
            agent_id: The ID of the agent to schedule
            cron_expression: Cron expression (e.g., "0 9 * * *" for 9 AM daily)

        Returns:
            True if scheduled successfully, False otherwise
        """
        try:
            # Validate cron expression
            if not self._validate_cron(cron_expression):
                logger.error(f"Invalid cron expression: {cron_expression}")
                return False

            # Parse cron expression to APScheduler trigger
            parts = cron_expression.split()
            if len(parts) == 5:
                minute, hour, day, month, dow = parts
            else:
                logger.error(f"Invalid cron format (need 5 parts): {cron_expression}")
                return False

            trigger = CronTrigger(
                minute=minute,
                hour=hour,
                day=day,
                month=month,
                day_of_week=dow,
            )

            # Remove existing job if any
            self.unschedule_agent(agent_id)

            # Add new job
            self.scheduler.add_job(
                self._run_agent,
                trigger=trigger,
                id=f"agent_{agent_id}",
                args=[agent_id],
                name=f"Scheduled run for agent {agent_id}",
            )

            logger.info(f"Scheduled agent {agent_id} with expression: {cron_expression}")
            return True

        except Exception as e:
            logger.error(f"Failed to schedule agent {agent_id}: {e}")
            return False

    def unschedule_agent(self, agent_id: str) -> bool:
        """
        Remove an agent from the schedule.

        Args:
            agent_id: The ID of the agent to unschedule

        Returns:
            True if unscheduled successfully, False otherwise
        """
        job_id = f"agent_{agent_id}"
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                self.scheduler.remove_job(job_id)
                logger.info(f"Unscheduled agent {agent_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unschedule agent {agent_id}: {e}")
            return False

    def get_next_run(self, agent_id: str) -> Optional[datetime]:
        """
        Get the next scheduled run time for an agent.

        Args:
            agent_id: The ID of the agent

        Returns:
            Next run datetime, or None if not scheduled
        """
        job_id = f"agent_{agent_id}"
        job = self.scheduler.get_job(job_id)
        if job and job.next_run_time:
            return job.next_run_time
        return None

    def get_scheduled_agents(self) -> Dict[str, datetime]:
        """
        Get all scheduled agents and their next run times.

        Returns:
            Dict mapping agent_id to next_run_time
        """
        result = {}
        for job in self.scheduler.get_jobs():
            if job.id.startswith("agent_"):
                agent_id = job.id[6:]  # Remove "agent_" prefix
                if job.next_run_time:
                    result[agent_id] = job.next_run_time
        return result

    def _validate_cron(self, expression: str) -> bool:
        """Validate a cron expression."""
        try:
            # Try to create a croniter to validate
            croniter(expression)
            return True
        except Exception:
            return False

    async def _run_agent(self, agent_id: str):
        """Execute the scheduled agent."""
        logger.info(f"Scheduled execution triggered for agent {agent_id}")

        if self._execute_callback:
            try:
                await self._execute_callback(agent_id, "schedule")
            except Exception as e:
                logger.error(f"Error executing scheduled agent {agent_id}: {e}")
        else:
            logger.warning(f"No execute callback set, skipping agent {agent_id}")

    def parse_human_schedule(self, schedule: str) -> Optional[str]:
        """
        Parse a human-readable schedule to a cron expression.

        Supports formats like:
        - "every 5 minutes"
        - "every hour"
        - "every day at 9am"
        - "every monday at 10:00"
        - "0 9 * * *" (raw cron)

        Returns:
            Cron expression, or None if invalid
        """
        schedule = schedule.lower().strip()

        # If it's already a cron expression, validate and return
        if len(schedule.split()) == 5:
            if self._validate_cron(schedule):
                return schedule

        # Parse human-readable formats
        if schedule.startswith("every "):
            schedule = schedule[6:]

            # Every X minutes
            if "minute" in schedule:
                parts = schedule.split()
                if parts[0].isdigit():
                    mins = int(parts[0])
                    return f"*/{mins} * * * *"
                return "* * * * *"  # Every minute

            # Every X hours
            if "hour" in schedule:
                parts = schedule.split()
                if parts[0].isdigit():
                    hours = int(parts[0])
                    return f"0 */{hours} * * *"
                return "0 * * * *"  # Every hour

            # Every day at X
            if "day at" in schedule:
                time_part = schedule.split("day at")[-1].strip()
                hour, minute = self._parse_time(time_part)
                return f"{minute} {hour} * * *"

            # Every day (no time)
            if schedule == "day":
                return "0 0 * * *"

            # Weekday schedules
            weekdays = {
                "monday": "1", "tuesday": "2", "wednesday": "3",
                "thursday": "4", "friday": "5", "saturday": "6", "sunday": "0",
            }
            for day, dow in weekdays.items():
                if day in schedule:
                    if " at " in schedule:
                        time_part = schedule.split(" at ")[-1].strip()
                        hour, minute = self._parse_time(time_part)
                        return f"{minute} {hour} * * {dow}"
                    return f"0 9 * * {dow}"  # Default to 9 AM

        return None

    def _parse_time(self, time_str: str) -> tuple:
        """Parse a time string like '9am', '10:30', '14:00'."""
        time_str = time_str.strip()

        # Handle AM/PM
        is_pm = "pm" in time_str.lower()
        time_str = time_str.lower().replace("am", "").replace("pm", "").strip()

        # Parse hour:minute
        if ":" in time_str:
            parts = time_str.split(":")
            hour = int(parts[0])
            minute = int(parts[1])
        else:
            hour = int(time_str) if time_str.isdigit() else 9
            minute = 0

        # Adjust for PM
        if is_pm and hour < 12:
            hour += 12

        return hour, minute


# Global scheduler instance
agent_scheduler = AgentScheduler()
