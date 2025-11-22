from marshmallow_dataclass import dataclass
from dataclasses import fields
from typing import List, Optional

from jm_networking.base_schema import BaseSchema


@dataclass(base_schema=BaseSchema)
class ExampleModel:

    id: Optional[int]  = None
    userId: Optional[int]  = None
    title: Optional[str]  = None
    completed: Optional[bool]  = None
