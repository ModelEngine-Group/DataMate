
from typing import Dict, Any

from datamate.core.base_op import Mapper


class TestMapper(Mapper):
    def execute(self, sample: Dict[str, Any]) -> Dict[str, Any]:
        sample[self.text_key] += "\n####################\n"
        return sample
