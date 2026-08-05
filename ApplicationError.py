import ipaddress
from dataclasses import dataclass
from option import Result, Ok, Err
from typing import List, Any

@dataclass
class ApplicationError:
    code: str
    message: str


def validate_mode(mode: str) -> Result[str, ApplicationError]:
    if mode not in ("blacklist", "whitelist"):
        return Err(ApplicationError(
            code="INVALID_MODE",
            message="Mode must be strictly either 'blacklist' or 'whitelist'."
        ))
    return Ok(mode)


def validate_values_array(values: Any) -> Result[List[Any], ApplicationError]:
    if not isinstance(values, list) or len(values) == 0:
        return Err(ApplicationError(
            code="INVALID_VALUES",
            message="Values must be a non-empty array."
        ))
    return Ok(values)


def validate_ids_array(ids: Any) -> Result[List[int], ApplicationError]:
    if not isinstance(ids, list) or len(ids) == 0:
        return Err(ApplicationError(
            code="INVALID_IDS",
            message="IDs must be a non-empty array of integers."
        ))
    

    if not all(isinstance(i, int) and not isinstance(i, bool) for i in ids):
        return Err(ApplicationError(
            code="INVALID_IDS",
            message="IDs must be a non-empty array of integers."
        ))
    return Ok(ids)


def validate_active_status(active: Any) -> Result[bool, ApplicationError]:
    if not isinstance(active, bool):
        return Err(ApplicationError(
            code="INVALID_ACTIVE_STATUS",
            message="Active must be a Boolean value (true or false)."
        ))
    return Ok(active)


def validate_ipv4(ip: str) -> Result[str, ApplicationError]:
    try:
        ipaddress.IPv4Address(ip)
        return Ok(ip)
    except (ipaddress.AddressValueError, ValueError):
        return Err(ApplicationError(
            code="INVALID_IPV4",
            message=f"'{ip}' is not a valid IPv4 address."
        ))


def validate_domain(domain: str) -> Result[str, ApplicationError]:
    if not isinstance(domain, str):
        return Err(ApplicationError(
            code="INVALID_DOMAIN", 
            message="Domain must be a string."
        ))


    if "://" in domain or "/" in domain or ":" in domain:
        return Err(ApplicationError(
            code="INVALID_DOMAIN",
            message=f"Domain '{domain}' must not include protocol, path, or port."
        ))
    
    return Ok(domain)


def validate_port(port: Any) -> Result[int, ApplicationError]:
    if not isinstance(port, int) or isinstance(port, bool):
        return Err(ApplicationError(
            code="INVALID_PORT",
            message="Ports must be integers between 1 and 65535."
        ))
        
    if not (1 <= port <= 65535):
        return Err(ApplicationError(
            code="INVALID_PORT",
            message="Ports must be integers between 1 and 65535."
        ))
        
    return Ok(port)
