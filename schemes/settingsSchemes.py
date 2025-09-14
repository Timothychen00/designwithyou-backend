from pydantic import BaseModel
from typing import Literal,Optional

from .knowledgeBaseSchemes import MainCategoriesUpdateScheme

class SettingsUpdateScheme(BaseModel):
    type:Literal['settings']="settings"
    category:Optional[MainCategoriesUpdateScheme] = None