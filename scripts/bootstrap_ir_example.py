import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from sdtm_adam_compiler.orchestration.spec_to_ir import build_ir_from_spec


if __name__ == "__main__":
    ir = build_ir_from_spec("data/specs/sdtm_spec_v1.csv", "SDTM")
    print(json.dumps(ir, default=lambda o: o.__dict__, indent=2))
