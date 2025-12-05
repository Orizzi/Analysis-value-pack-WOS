"""Core domain models."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ItemDefinition(BaseModel):
    item_id: str
    name: str
    category: str = "unknown"
    icon: Optional[str] = None
    base_value: Optional[float] = None
    description: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class PackItem(BaseModel):
    item_id: str
    name: str
    quantity: float
    category: str = "unknown"
    icon: Optional[str] = None
    base_value: Optional[float] = None
    source_row: Optional[int] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class Pack(BaseModel):
    pack_id: str
    name: str
    price: float = 0.0
    currency: str = "USD"
    source_file: str
    source_sheet: Optional[str] = None
    is_reference: bool = False
    tags: List[str] = Field(default_factory=list)
    items: List[PackItem] = Field(default_factory=list)
    notes: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class PackValuation(BaseModel):
    pack_id: str
    total_value: float
    price: float
    ratio: float
    score: float
    label: str
    color: str
    breakdown: Dict[str, float] = Field(default_factory=dict)


class ValuedPack(BaseModel):
    pack: Pack
    valuation: PackValuation
