from dataclasses import dataclass, field
from typing import Literal


DerivationType = Literal["direct_map", "hardcode", "conditional", "derive", "date_transform"]


@dataclass
class DerivationRule:
    kind: DerivationType
    expression: str
    sources: list[str] = field(default_factory=list)


@dataclass
class VariableRule:
    target_variable: str
    source_dataset: str = ""
    label: str = ""
    target_type: str = ""
    length: int | None = None
    derivation: DerivationRule | None = None
    codelist: list[str] = field(default_factory=list)


@dataclass
class DatasetPlan:
    dataset_name: str
    source_datasets: list[str] = field(default_factory=list)
    keys: list[str] = field(default_factory=list)
    variable_rules: list[VariableRule] = field(default_factory=list)


@dataclass
class CompilerIR:
    run_id: str
    spec_type: Literal["SDTM", "ADaM"]
    dataset_plans: list[DatasetPlan] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
