from pydantic import BaseModel
from typing import List, Optional


class ActionItem(BaseModel):
    title: str
    description: str
    assignee: Optional[str] = None
    priority: str
    type: str
    confidence: float


class BedrockOutput(BaseModel):
    summary: str
    action_items: List[ActionItem]
    categories: List[str]
    confidence: float