"""
WebSocket endpoints for real-time communication.
"""

import asyncio
import json
from typing import Dict, Set, List
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@dataclass
class LogEntry:
    """A log entry to broadcast."""
    timestamp: str
    level: str
    message: str
    source: str
    execution_id: str = ""


class ConnectionManager:
    """Manage WebSocket connections."""
    
    def __init__(self):
        # All log subscribers
        self.log_subscribers: Set[WebSocket] = set()
        # Execution-specific subscribers: execution_id -> set of websockets
        self.execution_subscribers: Dict[str, Set[WebSocket]] = {}
        # Log buffer for new subscribers
        self.log_buffer: List[LogEntry] = []
        self.max_buffer_size = 100
    
    async def connect_logs(self, websocket: WebSocket):
        """Connect a client to the log stream."""
        await websocket.accept()
        self.log_subscribers.add(websocket)
        
        # Send buffered logs
        for log in self.log_buffer[-50:]:
            try:
                await websocket.send_json(asdict(log))
            except Exception:
                pass
    
    async def connect_execution(self, websocket: WebSocket, execution_id: str):
        """Connect a client to a specific execution's log stream."""
        await websocket.accept()
        
        if execution_id not in self.execution_subscribers:
            self.execution_subscribers[execution_id] = set()
        self.execution_subscribers[execution_id].add(websocket)
    
    def disconnect_logs(self, websocket: WebSocket):
        """Disconnect a client from the log stream."""
        self.log_subscribers.discard(websocket)
    
    def disconnect_execution(self, websocket: WebSocket, execution_id: str):
        """Disconnect a client from an execution's log stream."""
        if execution_id in self.execution_subscribers:
            self.execution_subscribers[execution_id].discard(websocket)
            if not self.execution_subscribers[execution_id]:
                del self.execution_subscribers[execution_id]
    
    async def broadcast_log(self, log: LogEntry):
        """Broadcast a log entry to all subscribers."""
        # Add to buffer
        self.log_buffer.append(log)
        if len(self.log_buffer) > self.max_buffer_size:
            self.log_buffer = self.log_buffer[-self.max_buffer_size:]
        
        log_dict = asdict(log)
        
        # Broadcast to all log subscribers
        disconnected = set()
        for websocket in self.log_subscribers:
            try:
                await websocket.send_json(log_dict)
            except Exception:
                disconnected.add(websocket)
        
        for ws in disconnected:
            self.log_subscribers.discard(ws)
        
        # Broadcast to execution-specific subscribers
        if log.execution_id and log.execution_id in self.execution_subscribers:
            disconnected = set()
            for websocket in self.execution_subscribers[log.execution_id]:
                try:
                    await websocket.send_json(log_dict)
                except Exception:
                    disconnected.add(websocket)
            
            for ws in disconnected:
                self.execution_subscribers[log.execution_id].discard(ws)
    
    async def emit_log(
        self,
        level: str,
        message: str,
        source: str = "system",
        execution_id: str = "",
    ):
        """Emit a log entry."""
        log = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level=level,
            message=message,
            source=source,
            execution_id=execution_id,
        )
        await self.broadcast_log(log)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/logs")
async def websocket_logs(websocket: WebSocket):
    """
    WebSocket endpoint for real-time log streaming.
    Sends all system logs to connected clients.
    """
    await manager.connect_logs(websocket)
    
    try:
        while True:
            # Keep connection alive, receive pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_logs(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect_logs(websocket)


@router.websocket("/executions/{execution_id}/stream")
async def websocket_execution(websocket: WebSocket, execution_id: str):
    """
    WebSocket endpoint for streaming a specific execution's logs.
    """
    await manager.connect_execution(websocket, execution_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect_execution(websocket, execution_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect_execution(websocket, execution_id)


# Expose log emission for other modules
async def emit_system_log(level: str, message: str, source: str = "system"):
    """Emit a system-wide log."""
    await manager.emit_log(level, message, source)


async def emit_execution_log(execution_id: str, level: str, message: str, source: str = "agent"):
    """Emit an execution-specific log."""
    await manager.emit_log(level, message, source, execution_id)
