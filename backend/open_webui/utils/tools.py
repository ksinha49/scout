import inspect
import logging
import re

from typing import Any, Awaitable, Callable, Literal, get_type_hints
from functools import update_wrapper, partial


from fastapi import Request
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    create_model,
    field_validator,
)
from langchain_core.utils.function_calling import convert_to_openai_function


from open_webui.models.tools import Tools
from open_webui.models.users import UserModel
from open_webui.utils.plugin import load_tools_module_by_id

log = logging.getLogger(__name__)


class ToolParameter(BaseModel):
    """Specification for a single tool parameter."""

    type: Literal[
        "string",
        "number",
        "integer",
        "boolean",
        "array",
        "object",
    ]
    description: str | None = None

    model_config = ConfigDict(extra="allow")


class ToolParameters(BaseModel):
    """Container for tool parameter definitions."""

    type: str = "object"
    properties: dict[str, ToolParameter] = Field(default_factory=dict)
    required: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="allow")

    @field_validator("properties", mode="before")
    @classmethod
    def _exclude_internal(cls, v: dict) -> dict:
        return {k: val for k, val in v.items() if not k.startswith("__")}


class ToolSpec(BaseModel):
    """Model representing a single tool specification."""

    name: str
    description: str | None = None
    parameters: ToolParameters

    model_config = ConfigDict(extra="allow")


def apply_extra_params_to_tool_function(
    function: Callable, extra_params: dict
) -> Callable[..., Awaitable]:
    sig = inspect.signature(function)
    extra_params = {k: v for k, v in extra_params.items() if k in sig.parameters}
    partial_func = partial(function, **extra_params)
    if inspect.iscoroutinefunction(function):
        update_wrapper(partial_func, function)
        return partial_func

    async def new_function(*args, **kwargs):
        return partial_func(*args, **kwargs)

    update_wrapper(new_function, function)
    return new_function


# Mutation on extra_params
def get_tools(
    request: Request, tool_ids: list[str], user: UserModel, extra_params: dict
) -> dict[str, dict]:
    tools_dict = {}

    for tool_id in tool_ids:
        tools = Tools.get_tool_by_id(tool_id)
        if tools is None:
            continue

        module = request.app.state.TOOLS.get(tool_id, None)
        if module is None:
            module, _ = load_tools_module_by_id(tool_id)
            request.app.state.TOOLS[tool_id] = module

        extra_params["__id__"] = tool_id
        if hasattr(module, "valves") and hasattr(module, "Valves"):
            valves = Tools.get_tool_valves_by_id(tool_id) or {}
            module.valves = module.Valves(**valves)

        if hasattr(module, "UserValves"):
            extra_params["__user__"]["valves"] = module.UserValves(  # type: ignore
                **Tools.get_user_valves_by_id_and_user_id(tool_id, user.id)
            )

        for spec_dict in tools.specs:
            try:
                spec_model = ToolSpec.model_validate(spec_dict)
            except ValidationError as e:
                log.warning(f"Invalid spec for tool {tool_id}: {e}")
                continue

            spec = spec_model.model_dump()
            function_name = spec_model.name

            # convert to function that takes only model params and inserts custom params
            original_func = getattr(module, function_name)
            callable = apply_extra_params_to_tool_function(original_func, extra_params)

            if callable.__doc__ and callable.__doc__.strip() != "":
                s = re.split(":(param|return)", callable.__doc__, 1)
                spec["description"] = s[0]
            else:
                spec["description"] = function_name

            # TODO: This needs to be a pydantic model
            tool_dict = {
                "spec": spec,
                "callable": callable,
                "toolkit_id": tool_id,
                "pydantic_model": function_to_pydantic_model(callable),
                # Misc info
                "file_handler": hasattr(module, "file_handler") and module.file_handler,
                "citation": hasattr(module, "citation") and module.citation,
            }

            if function_name in tools_dict:
                log.warning(
                    f"Tool {function_name} already exists; prefixing with {tool_id}."
                )
                function_name = f"{tool_id}_{function_name}"
                spec["name"] = function_name
                tool_dict["spec"] = spec

            tools_dict[function_name] = tool_dict

    return tools_dict


def parse_description(docstring: str | None) -> str:
    """
    Parse a function's docstring to extract the description.

    Args:
        docstring (str): The docstring to parse.

    Returns:
        str: The description.
    """

    if not docstring:
        return ""

    lines = [line.strip() for line in docstring.strip().split("\n")]
    description_lines: list[str] = []

    for line in lines:
        if re.match(r":param", line) or re.match(r":return", line):
            break

        description_lines.append(line)

    return "\n".join(description_lines)


def parse_docstring(docstring):
    """
    Parse a function's docstring to extract parameter descriptions in reST format.

    Args:
        docstring (str): The docstring to parse.

    Returns:
        dict: A dictionary where keys are parameter names and values are descriptions.
    """
    if not docstring:
        return {}

    # Regex to match `:param name: description` format
    param_pattern = re.compile(r":param (\w+):\s*(.+)")
    param_descriptions = {}

    for line in docstring.splitlines():
        match = param_pattern.match(line.strip())
        if not match:
            continue
        param_name, param_description = match.groups()
        if param_name.startswith("__"):
            continue
        param_descriptions[param_name] = param_description

    return param_descriptions


def function_to_pydantic_model(func: Callable) -> type[BaseModel]:
    """
    Converts a Python function's type hints and docstring to a Pydantic model,
    including support for nested types, default values, and descriptions.

    Args:
        func: The function whose type hints and docstring should be converted.
        model_name: The name of the generated Pydantic model.

    Returns:
        A Pydantic model class.
    """
    type_hints = get_type_hints(func)
    signature = inspect.signature(func)
    parameters = signature.parameters

    docstring = func.__doc__
    descriptions = parse_docstring(docstring)

    tool_description = parse_description(docstring)

    field_defs = {}
    for name, param in parameters.items():
        type_hint = type_hints.get(name, Any)
        default_value = param.default if param.default is not param.empty else ...
        description = descriptions.get(name, None)
        if not description:
            field_defs[name] = type_hint, default_value
            continue
        field_defs[name] = type_hint, Field(default_value, description=description)

    model = create_model(func.__name__, **field_defs)
    model.__doc__ = tool_description

    return model


def get_callable_attributes(tool: object) -> list[Callable]:
    return [
        getattr(tool, func)
        for func in dir(tool)
        if callable(getattr(tool, func))
        and not func.startswith("__")
        and not inspect.isclass(getattr(tool, func))
    ]


def get_tools_specs(tool_class: object) -> list[dict]:
    function_list = get_callable_attributes(tool_class)
    models = map(function_to_pydantic_model, function_list)
    return [convert_to_openai_function(tool) for tool in models]
