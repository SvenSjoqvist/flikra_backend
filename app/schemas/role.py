from pydantic import BaseModel
from typing import Optional

class RoleBase(BaseModel):
    name: str

class RoleCreate(RoleBase):
    pass

class RoleUpdate(BaseModel):
    name: Optional[str] = None

class Role(RoleBase):
    id: int

    class Config:
        from_attributes = True 