from pydantic import BaseModel, Field

class GenerateRequest(BaseModel):
    roadmap_id: str
    known_node_ids: list[str] = Field(default_factory=list)
    duration_weeks: int = Field(gt=0)
    hours_per_week: float = Field(gt=0.0)

class StalenessRequest(BaseModel):
    roadmap_id: str
    version_generated_against: str
    node_ids_used: list[str]
