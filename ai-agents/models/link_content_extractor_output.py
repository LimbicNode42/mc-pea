"""
Compact Pydantic models for API Link Content Extractor output.
Optimized field names for token efficiency with unique identifiers for easy searching.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class ApiParameter(BaseModel):
    pn: str = Field(description="Parameter name")
    pd: str = Field(description="Parameter description")
    pr: bool = Field(default=False, description="Required flag")
    pt: str = Field(description="Parameter type")
    pv: Optional[str] = Field(default=None, description="Default value")

class ApiLinkContentExtractorPoint(BaseModel):
    en: str = Field(description="Endpoint name")
    ed: str = Field(description="Endpoint description")
    em: str = Field(description="HTTP method")
    ep: str = Field(description="API path")
    ecp: List[str] = Field(default_factory=list, description="Category path")
    esu: Optional[str] = Field(default=None, description="Source URL")
    eh: List[ApiParameter] = Field(default_factory=list, description="Headers")
    epp: List[ApiParameter] = Field(default_factory=list, description="Path params")
    eqp: List[ApiParameter] = Field(default_factory=list, description="Query params")
    ebp: List[ApiParameter] = Field(default_factory=list, description="Body params")
    erc: Dict[str, str] = Field(default_factory=dict, description="Response codes")
    ere: Dict[str, str] = Field(default_factory=dict, description="Response fields")

class ApiLinkContentExtractorCategory(BaseModel):
    cn: str = Field(description="Category name")
    cd: str = Field(description="Category description")
    ces: List[ApiLinkContentExtractorPoint] = Field(default_factory=list, description="Endpoints")
    
class ApiLinkContentExtractorOutput(BaseModel):
    ocs: List[ApiLinkContentExtractorCategory] = Field(description="Output categories")