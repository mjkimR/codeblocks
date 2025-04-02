from pydantic import BaseModel
from typing import Optional, List

from make_partial import make_partial_model


async def test_make_partial_model():
    class TestModel(BaseModel):
        field1: int
        field2: str

    PartialTestModel = make_partial_model(TestModel)

    assert PartialTestModel.model_fields['field1'].default is None
    assert PartialTestModel.model_fields['field2'].default is None
    assert PartialTestModel.model_fields['field1'].annotation == Optional[int]
    assert PartialTestModel.model_fields['field2'].annotation == Optional[str]


async def test_partial_model_with_default_values():
    class AdvancedTestModel(BaseModel):
        field1: int
        field2: str = "default"
        field3: Optional[List[str]] = None

    PartialAdvancedTestModel = make_partial_model(AdvancedTestModel)

    assert PartialAdvancedTestModel.model_fields['field1'].default is None
    assert PartialAdvancedTestModel.model_fields['field2'].default == "default"
    assert PartialAdvancedTestModel.model_fields['field3'].default is None

    assert PartialAdvancedTestModel.model_fields['field1'].annotation == Optional[int]
    assert PartialAdvancedTestModel.model_fields['field2'].annotation == Optional[str]
    assert PartialAdvancedTestModel.model_fields['field3'].annotation == Optional[List[str]]


async def test_empty_model():
    class EmptyModel(BaseModel):
        pass

    PartialEmptyModel = make_partial_model(EmptyModel)
    assert len(PartialEmptyModel.model_fields) == 0


async def test_nested_model():
    class NestedModel(BaseModel):
        inner_field: int

    class ParentModel(BaseModel):
        nested: NestedModel
        other_field: str

    PartialParentModel = make_partial_model(ParentModel)
    assert PartialParentModel.model_fields['nested'].annotation == Optional[NestedModel]
    assert PartialParentModel.model_fields['other_field'].annotation == Optional[str]
