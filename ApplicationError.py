from dataclasses import dataclass
from option import Result, Ok, Err
from enum import Enum
from typing import List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationError, IPv4Address

# ==========================================
# 1. מחלקת השגיאה (נשארת ללא שינוי)
# ==========================================
@dataclass
class ApplicationError:
    code: str
    message: str

# ==========================================
# 2. הגדרות ולידציה בסיסיות (Enums)
# ==========================================
class RuleMode(str, Enum):
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"

# ==========================================
# 3. מודלים של Pydantic (מחליפים את הבדיקות הידניות)
# ==========================================
class BaseFirewallRequest(BaseModel):
    # הגדרות מחמירות לכל המודלים: אוסר המרת סוגים אוטומטית ואוסר שדות לא מוכרים
    model_config = ConfigDict(strict=True, extra="forbid")

class AddIPsRequest(BaseFirewallRequest):
    # Pydantic בודק אוטומטית שמדובר ב-IPv4 חוקי ושזו רשימה לא ריקה
    values: List[IPv4Address] = Field(..., min_length=1)
    mode: RuleMode

class AddDomainsRequest(BaseFirewallRequest):
    values: List[str] = Field(..., min_length=1)
    mode: RuleMode

    @field_validator("values")
    @classmethod
    def validate_domains(cls, domains: List[str]) -> List[str]:
        for domain in domains:
            if "://" in domain or "/" in domain or ":" in domain:
                raise ValueError(f"Domain '{domain}' must not include protocol, path, or port.")
        return domains

class AddPortsRequest(BaseFirewallRequest):
    values: List[int] = Field(..., min_length=1)
    mode: RuleMode

    @field_validator("values")
    @classmethod
    def validate_ports(cls, ports: List[int]) -> List[int]:
        for port in ports:
            # Pydantic כבר וידא שזה int (בגלל strict=True), אנחנו רק בודקים את הטווח
            if not (1 <= port <= 65535):
                raise ValueError(f"Port {port} must be between 1 and 65535.")
        return ports

class RemoveRulesRequest(BaseFirewallRequest):
    ids: List[int] = Field(..., min_length=1)

class UpdateStatusRequest(BaseFirewallRequest):
    ids: List[int] = Field(..., min_length=1)
    active: bool

# ==========================================
# 4. פונקציית הגבול (מחברת הכל יחד)
# ==========================================
def validate_request_payload(model_cls: type[BaseModel], payload: Dict[str, Any]) -> Result[BaseModel, ApplicationError]:
    """
    פונקציה גנרית שמקבלת מילון (או JSON), מריצה אותו דרך המודל של Pydantic,
    ומחזירה Ok עם הנתונים המאומתים או Err עם ApplicationError.
    """
    try:
        # Pydantic מבצע את כל הוולידציות בשורה אחת
        validated_data = model_cls.model_validate(payload)
        return Ok(validated_data)

    except ValidationError as e:
        # אם Pydantic מצא שגיאה - אנחנו מתרגמים אותה ל-ApplicationError שלנו
        first_error = e.errors()[0]
        
        # בניית קוד שגיאה דינמי (למשל: INVALID_MODE, INVALID_VALUES, וכו')
        error_loc = str(first_error["loc"][-1]).upper() if first_error["loc"] else "INPUT"
        error_code = f"INVALID_{error_loc}"
        
        return Err(ApplicationError(
            code=error_code,
            message=first_error["msg"]
        ))
