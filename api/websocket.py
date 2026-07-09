from fastapi import WebSocket
from typing import List
import json
import asyncio
from runtime.logger import get_logger

logger = get_logger("nexusguard.websocket")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"Client disconnected. Total clients: {len(self.active_connections)}")

    async def broadcast_incident(self, event: dict):
        dead_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(event))
            except Exception as e:
                logger.error(f"Failed to send to websocket: {e}")
                dead_connections.append(connection)
                
        for connection in dead_connections:
            self.disconnect(connection)

manager = ConnectionManager()
