import os
import json
from datetime import datetime
from typing import List, Optional
from uuid import uuid4

import asyncpg

from models.command import Command, CommandCreate, CommandStatus


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://postgres:postgres@localhost:5432/command"
        )

    async def connect(self):
        self.pool = await asyncpg.create_pool(self.database_url)
        print("Connected to database")

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            print("Disconnected from database")

    async def create_command(self, command: CommandCreate) -> Command:
        command_id = str(uuid4())
        query = """
            INSERT INTO commands (command_id, device_id, action, params, status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING id, command_id, device_id, action, params, status, created_at, executed_at
        """
        params_json = json.dumps(command.params) if command.params else None
        row = await self.pool.fetchrow(
            query,
            command_id,
            command.device_id,
            command.action,
            params_json,
            CommandStatus.PENDING.value,
            datetime.utcnow()
        )
        return self._row_to_command(row)

    async def get_commands(
        self,
        device_id: Optional[str] = None,
        status: Optional[CommandStatus] = None,
        limit: int = 100
    ) -> List[Command]:
        query = "SELECT * FROM commands WHERE 1=1"
        params = []
        param_count = 0

        if device_id:
            param_count += 1
            query += f" AND device_id = ${param_count}"
            params.append(device_id)

        if status:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(status.value)

        query += f" ORDER BY created_at DESC LIMIT {limit}"

        rows = await self.pool.fetch(query, *params)
        return [self._row_to_command(row) for row in rows]

    async def get_command_by_id(self, command_id: str) -> Optional[Command]:
        query = "SELECT * FROM commands WHERE command_id = $1"
        row = await self.pool.fetchrow(query, command_id)
        if row:
            return self._row_to_command(row)
        return None

    async def update_command_status(
        self,
        command_id: str,
        status: CommandStatus,
        executed_at: Optional[datetime] = None
    ):
        query = """
            UPDATE commands
            SET status = $1, executed_at = $2
            WHERE command_id = $3
        """
        await self.pool.execute(query, status.value, executed_at, command_id)

    def _row_to_command(self, row) -> Command:
        params = None
        if row["params"]:
            params = json.loads(row["params"]) if isinstance(row["params"], str) else row["params"]
        
        return Command(
            id=row["id"],
            command_id=row["command_id"],
            device_id=row["device_id"],
            action=row["action"],
            params=params,
            status=CommandStatus(row["status"]),
            created_at=row["created_at"],
            executed_at=row["executed_at"]
        )
