from dataclasses import dataclass
from option import Result, Ok, Err

@dataclass
class ApplicationError:
    code: str
    message: str


def start_server(port: int) -> Result[str, ApplicationError]:


    if not isinstance(port, int):
        return Err(ApplicationError(
            code="INVALID_TYPE",
            message="The port must be an integer."
        ))

    if not (1024 <= port <= 65535):
        return Err(ApplicationError(
            code="INVALID_PORT",
            message=f"Port {port} is forbidden. Must be between 1024 and 65535."
        ))


    if port == 8080:
        return Err(ApplicationError(
            code="PORT_IN_USE",
            message=f"Port {port} is already in use by another process."
        ))


    return Ok(f"Server successfully started on port {port}.")