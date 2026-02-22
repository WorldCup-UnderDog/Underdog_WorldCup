"""Team schemas."""

from pydantic import BaseModel


class TeamListResponse(BaseModel):
    teams: list[str]

