from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class PlaceholderData(BaseModel):
    category: str
    placement: str = "inline" # "inline" or "standalone" 
    data: Any = None
    latex: Optional[str] = None
    raw_omml: Optional[str] = None
    is_display: bool = False

class Option(BaseModel):
    label: str  # A, B, C, D
    text: str
    is_structural: bool = False

class TableRow(BaseModel):
    cells: List[str]

class TableData(BaseModel):
    rows: List[TableRow]

class Question(BaseModel):
    number: int
    text: str
    options: List[Option] = Field(default_factory=list)
    is_structural: bool = False

class Section(BaseModel):
    name: str  # PHYSICS, CHEMISTRY, BIOLOGY
    sub_section: Optional[str] = None  # SECTION-A, SECTION-B
    questions: List[Question] = Field(default_factory=list)

class ParsedDocument(BaseModel):
    title: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    sections: List[Section] = Field(default_factory=list)
    placeholders: Dict[str, PlaceholderData] = Field(default_factory=dict)
