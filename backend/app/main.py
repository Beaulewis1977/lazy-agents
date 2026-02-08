"""
LazyAgents API Server
Main FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings
from app.core.database import init_db
from app.api import agents, skills, integrations, executions, health, websocket, mcp
from app.mcp import MCPServerManager

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting LazyAgents API", version=settings.APP_VERSION)
    await init_db()
    logger.info("Database initialized")

    app.state.mcp_manager = MCPServerManager()
    await app.state.mcp_manager.start_enabled_servers()
    logger.info("MCP lifecycle manager initialized")
    
    # Start scheduler
    from app.runtime.scheduler import agent_scheduler
    from app.core.database import async_session
    from app.runtime.agent_executor import AgentExecutor
    
    async def execute_scheduled_agent(agent_id: str, trigger: str):
        """Callback for scheduled agent execution."""
        async with async_session() as db:
            executor = AgentExecutor(db)
            try:
                await executor.execute(agent_id, trigger=trigger)
            except Exception as e:
                logger.error("Scheduled execution failed", agent_id=agent_id, error=str(e))
    
    agent_scheduler.set_execute_callback(execute_scheduled_agent)
    agent_scheduler.start()
    logger.info("Agent scheduler started")
    
    # Load existing schedules
    from sqlalchemy import select
    from app.models.agent import Agent
    
    async with async_session() as db:
        result = await db.execute(
            select(Agent).where(
                Agent.status == "active",
                Agent.schedule.isnot(None),
                Agent.schedule != ""
            )
        )
        scheduled_count = 0
        for agent in result.scalars().all():
            if agent_scheduler.schedule_agent(agent.id, agent.schedule):
                scheduled_count += 1
        logger.info(f"Loaded {scheduled_count} scheduled agents")
    
    # Emit startup log via WebSocket
    await websocket.emit_system_log("info", f"LazyAgents into loaded with {scheduled_count} schedules")
    
    yield
    
    # Shutdown
    await app.state.mcp_manager.shutdown_all()
    logger.info("MCP lifecycle manager shut down")
    agent_scheduler.stop()
    logger.info("Shutting down LazyAgents API")


# Create FastAPI application
app = FastAPI(
    title="LazyAgents API",
    description="AI Agent Orchestration Platform for Indie Developers",
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, tags=["Health"])
app.include_router(agents.router, prefix="/api/agents", tags=["Agents"])
app.include_router(skills.router, prefix="/api/skills", tags=["Skills"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"])
app.include_router(executions.router, prefix="/api/executions", tags=["Executions"])
app.include_router(mcp.router, tags=["MCP"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "LazyAgents API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }
