from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from datetime import datetime, timezone


class Article(BaseModel):
    """Normalized article schema for all sources"""

    title: str = Field(..., min_length=1, max_length=1000)
    content: str = Field(..., min_length=1, max_length=50000)
    source: str = Field(..., description="newsapi, csv, or web")
    url: str = Field(default="N/A")
    fetched_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self):
        return self.model_dump()

    @classmethod
    def validate_source(cls, source: str):
        """Validate that source is one of allowed values"""
        if source not in ["newsapi", "csv", "web"]:
            raise ValueError(f"Invalid source: {source}. Must be newsapi, csv, or web.")
