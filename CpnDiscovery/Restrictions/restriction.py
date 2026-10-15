import json
from enum import Enum


class OptionalOTRestriction:

    def __init__(self, transition: str, otype: str):
        self.transition = transition
        self.otype = otype

    def to_dict(self) -> dict:
        return {"transition": self.transition, "otype": self.otype}

    @classmethod
    def from_dict(cls, data: dict) -> "OptionalOTRestriction":
        return cls(transition=data["transition"], otype=data["otype"])


class NarrowVariableArcRestriction:

    def __init__(
        self,
        transition: str,
        type: str,
        range: tuple[int, int],
        otype: str,
    ):
        self.transition = transition
        self.otype = otype
        self.range = tuple(range)
        self.type = type

    def to_dict(self) -> dict:
        return {
            "transition": self.transition,
            "type": self.type,
            "range": list(self.range),
            "otype": self.otype,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "NarrowVariableArcRestriction":
        return cls(
            transition=data["transition"],
            type=data["type"],
            range=tuple(data["range"]),
            otype=data["otype"],
        )


class SyncType(Enum):
    IMPLICATION = 0
    SYMETRIC = 1


class SynchronizationRestriction:

    def __init__(
        self,
        transitions: list[str],
        sync_type: SyncType,
        type_a: str,
        type_b: str,
    ):
        self.transitions = transitions
        self.sync_type = (
            sync_type
            if isinstance(sync_type, SyncType)
            else SyncType[sync_type]
        )
        self.type_a = type_a
        self.type_b = type_b

    def __str__(self):
        return f"<{self.type_a} & {self.type_b} | {self.sync_type} | {self.transitions}>"

    def to_dict(self) -> dict:
        return {
            "class_type": self.__class__.__name__,
            "transitions": list(self.transitions),
            "sync_type": self.sync_type.name,
            "type_a": self.type_a,
            "type_b": self.type_b,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SynchronizationRestriction":
        # Handle subclass detection if ExtendedSynchronizationRestriction is present
        target_cls = (
            ExtendedSynchronizationRestriction
            if data.get("class_type") == "ExtendedSynchronizationRestriction"
            else cls
        )
        return target_cls(
            transitions=set(data["transitions"]),
            sync_type=SyncType[data["sync_type"]],
            type_a=data["type_a"],
            type_b=data["type_b"],
        )


class ExtendedSynchronizationRestriction(SynchronizationRestriction):

    def __init__(
        self,
        transitions: list[str],
        sync_type: SyncType,
        type_a: str,
        type_b: str,
    ):
        super().__init__(transitions, sync_type, type_a, type_b)


class RestrictionCollection:

    def __init__(self):
        self.narrow_var_arcs: list[NarrowVariableArcRestriction] = []
        self.optional_ot: list[OptionalOTRestriction] = []
        self.synchronizations: list[SynchronizationRestriction] = []

    def to_dict(self) -> dict:
        return {
            "narrow_var_arcs": [item.to_dict() for item in self.narrow_var_arcs],
            "optional_ot": [item.to_dict() for item in self.optional_ot],
            "synchronizations": [item.to_dict() for item in self.synchronizations],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RestrictionCollection":
        collection = cls()
        collection.narrow_var_arcs = [
            NarrowVariableArcRestriction.from_dict(item)
            for item in data.get("narrow_var_arcs", [])
        ]
        collection.optional_ot = [
            OptionalOTRestriction.from_dict(item)
            for item in data.get("optional_ot", [])
        ]
        collection.synchronizations = [
            SynchronizationRestriction.from_dict(item)
            for item in data.get("synchronizations", [])
        ]
        return collection

    # JSON File and String helper methods
    def to_json(self, filepath: str | None = None, indent: int = 2) -> str:
        """Serializes the collection to a JSON string or saves to file if filepath is given."""
        data = self.to_dict()
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent)
            return ""
        return json.dumps(data, indent=indent)

    @classmethod
    def from_json(cls, source: str, is_filepath: bool = True) -> "RestrictionCollection":
        """Deserializes from a JSON string or JSON file path."""
        if is_filepath:
            with open(source, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = json.loads(source)
        return cls.from_dict(data)