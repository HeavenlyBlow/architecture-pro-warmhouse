from typing import List, Optional

from fastapi import APIRouter, HTTPException, Request, Query

from models.command import CommandCreate, CommandResponse, CommandStatus

router = APIRouter()


@router.get(
    "",
    response_model=List[CommandResponse],
    summary="Get commands list",
    description="Получить список команд с фильтрацией по device_id и status"
)
async def get_commands(
    request: Request,
    device_id: Optional[str] = Query(None, description="Filter by device ID"),
    status: Optional[CommandStatus] = Query(None, description="Filter by status")
):
    db = request.app.state.db
    commands = await db.get_commands(device_id=device_id, status=status)
    return [
        CommandResponse(
            command_id=cmd.command_id,
            device_id=cmd.device_id,
            action=cmd.action,
            params=cmd.params,
            status=cmd.status,
            created_at=cmd.created_at,
            executed_at=cmd.executed_at
        )
        for cmd in commands
    ]


@router.post(
    "",
    response_model=CommandResponse,
    status_code=201,
    summary="Send command to device",
    description="Отправить команду устройству. Команда сохраняется в БД и публикуется в MQTT."
)
async def create_command(request: Request, command: CommandCreate):
    db = request.app.state.db
    mqtt = request.app.state.mqtt

    cmd = await db.create_command(command)

    published = await mqtt.publish_command(
        device_id=cmd.device_id,
        command_id=cmd.command_id,
        action=cmd.action,
        params=cmd.params or {}
    )

    if published:
        await db.update_command_status(cmd.command_id, CommandStatus.SENT)
        cmd.status = CommandStatus.SENT

    return CommandResponse(
        command_id=cmd.command_id,
        device_id=cmd.device_id,
        action=cmd.action,
        params=cmd.params,
        status=cmd.status,
        created_at=cmd.created_at,
        executed_at=cmd.executed_at
    )


@router.get(
    "/{command_id}",
    response_model=CommandResponse,
    summary="Get command by ID",
    description="Получить информацию о команде по её ID"
)
async def get_command(request: Request, command_id: str):
    db = request.app.state.db
    cmd = await db.get_command_by_id(command_id)
    
    if not cmd:
        raise HTTPException(status_code=404, detail="Command not found")

    return CommandResponse(
        command_id=cmd.command_id,
        device_id=cmd.device_id,
        action=cmd.action,
        params=cmd.params,
        status=cmd.status,
        created_at=cmd.created_at,
        executed_at=cmd.executed_at
    )
