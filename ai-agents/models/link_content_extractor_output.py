"""
Compact Pydantic models for API Link Content Extractor output.
Optimized field names for token efficiency: n=name, d=desc, m=method, p=path, etc.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ApiParameter(BaseModel):
    n: str = Field(description="Parameter name")
    d: str = Field(description="Parameter description")
    r: bool = Field(default=False, description="Required flag")
    t: str = Field(description="Parameter type")
    v: Optional[str] = Field(default=None, description="Default value")

class ApiLinkContentExtractorPoint(BaseModel):
    n: str = Field(description="Endpoint name")
    d: str = Field(description="Endpoint description")
    m: str = Field(description="HTTP method")
    p: str = Field(description="API path")
    cp: List[str] = Field(default_factory=list, description="Category path")
    su: Optional[str] = Field(default=None, description="Source URL")
    h: List[ApiParameter] = Field(default_factory=list, description="Headers")
    pp: List[ApiParameter] = Field(default_factory=list, description="Path params")
    qp: List[ApiParameter] = Field(default_factory=list, description="Query params")
    bp: List[ApiParameter] = Field(default_factory=list, description="Body params")
    rc: Dict[str, str] = Field(default_factory=dict, description="Response codes")

class ApiLinkContentExtractorCategory(BaseModel):
    n: str = Field(description="Category name")
    d: str = Field(description="Category description")
    es: List[ApiLinkContentExtractorPoint] = Field(default_factory=list, description="Endpoints")
    
class ApiLinkContentExtractorOutput(BaseModel):
    cs: List[ApiLinkContentExtractorCategory] = Field(description="Categories")