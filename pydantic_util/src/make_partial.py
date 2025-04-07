from copy import deepcopy
from typing import Any, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, create_model
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined


def _make_field_optional(field: FieldInfo, default: Any = None) -> Tuple[Any, FieldInfo]:
    """
    Make a field optional by modifying its default value and annotation.

    Args:
        field (FieldInfo): The field information object to modify.
        default (Any, optional): The default value for the field. Defaults to None.

    Returns:
        Tuple[Any, FieldInfo]: A tuple containing the updated annotation and field information.
    """
    new = deepcopy(field)
    if default == PydanticUndefined:
        new.default = None
    else:
        new.default = default

    new.annotation = Optional[field.annotation]
    return new.annotation, new


_BaseModelT = TypeVar('_BaseModelT', bound=BaseModel)


def make_partial_model(model: Type[_BaseModelT], model_name=None) -> Type[_BaseModelT]:
    """
    Create a new model where all fields of the given model are optional.

    Args:
        model (Type[_BaseModelT]): The base model class to make partial.
        model_name (str, optional): The name for the new model. If not provided,
            the name of the base model will be used. Defaults to None.

    Returns:
        Type[_BaseModelT]: The newly created partial model with optional fields.
    """
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
