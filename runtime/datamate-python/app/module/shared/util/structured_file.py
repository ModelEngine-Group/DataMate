import json

from enum import Enum
from jsonschema import validate

class ItemTypes(Enum):
    QA = "QA"


class StructuredFileItemHandler:
    def __init__(self):
        pass

    def get_item_type(self) -> ItemTypes:
        pass

    def get_items_from_file(self, file_path: str) -> list[dict]:
        pass

    def check_file(self) -> bool:
        pass

class QAItemHandler(StructuredFileItemHandler):
    def __init__(self):
        self.schema_alpaca = {
            "type": "object",
            "properties": {
                "instruction": {"type": "string"},
                "input": {"type": "string"},
                "output": {"type": "string"}
            },
            "required": ["instruction", "output"],
        }
        self.schema_alpaca_list = {
            "type": "array",
            "items": self.schema_alpaca,
        }
        super().__init__()

    def get_item_type(self):
        return ItemTypes.QA

    def validate_json(self, data):
        try:
            validate(instance=data, schema=self.schema_alpaca)
            return True
        except Exception as e:
            try:
                validate(instance=data, schema=self.schema_alpaca_list)
                return True
            except Exception as e:
                return False

    def get_items_from_file(self, file_path: str) -> list[dict]:
        file_type = file_path.split(".")[-1].upper()
        items = []
        if file_type == "JSON":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if not self.validate_json(data):
                    return items
                items = data
        elif file_type == "JSONL":
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    if not self.validate_json(data):
                        continue
                    items.append(data)
        return items

    def check_file(self) -> bool:
        pass


class StructuredFileHandlerFactory:
    def __init__(self):
        self.handlers: list[StructuredFileItemHandler] = []
        self.handlers.append(QAItemHandler())

    def get_handler(self, item_type: str) -> StructuredFileItemHandler:
        for handler in self.handlers:
            if handler.get_item_type().value == item_type:
                return handler
        raise ValueError(f"Unsupported item type: {item_type}")
