from copy import deepcopy
from typing import Any, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined


def _make_field_optional(field: FieldInfo, default: Any = None) -> Tuple[Any, FieldInfo]:
    """Make a field optional"""
    new = deepcopy(field)
    if default == PydanticUndefined:
        new.default = None
    else:
        new.default = default

    new.annotation = Optional[field.annotation]
    return (new.annotation, new)


_BaseModelT = TypeVar('_BaseModelT', bound=BaseModel)


def make_partial_model(model: Type[_BaseModelT], model_name=None) -> Type[_BaseModelT]:
    """Make all fields in a model optional"""
    return create_model(
        model.__name__ if model_name is None else model_name,
        __base__=model,
        __module__=model.__module__,
        **{
            field_name: _make_field_optional(
                field_info, default=field_info.default
            )
            for field_name, field_info in model.model_fields.items()
        }
    )
