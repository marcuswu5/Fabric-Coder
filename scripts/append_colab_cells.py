import json
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "FineTuning.ipynb"
nb = json.loads(p.read_text(encoding="utf-8"))
existing = {c.get("metadata", {}).get("id") for c in nb["cells"]}
if "fabric-test-suite-setup" in existing:
    print("Colab test_suite cells already present; skipping")
    raise SystemExit(0)
if (
    nb["cells"]
    and nb["cells"][-1]["cell_type"] == "code"
    and not "".join(nb["cells"][-1].get("source", [])).strip()
):
    nb["cells"].pop()

md = """## test_suite: Colab Java benchmark

Run **Setup** once per Colab runtime after you have this repo on the VM (clone or Drive). Then load your model as usual and run **Benchmark** — it uses `model` and `tokenizer` from earlier cells (device is taken from the model).

Set `REPO_ROOT` to the folder that contains `test_suite/` (default `/content/Fabric-Coder`).
"""

setup = r"""# test_suite: one-time runtime prep (Java + PyYAML + paths)
import subprocess, sys
from pathlib import Path

subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pyyaml"])

REPO_ROOT = Path("/content/Fabric-Coder")  # change if you cloned elsewhere
TEST_SUITE = REPO_ROOT / "test_suite"
sys.path.insert(0, str(TEST_SUITE))

import colab_eval
colab_eval.install_colab_java()
colab_eval.prepare_runtime(TEST_SUITE)

assert TEST_SUITE.is_dir(), f"Missing {TEST_SUITE} — clone repo or upload Fabric-Coder"
print("TEST_SUITE =", TEST_SUITE)
print("java:", subprocess.run(["java", "-version"], capture_output=True, text=True).stderr.splitlines()[:1])
"""

bench = r"""# test_suite: run JUnit checks on model completions (expects `model` and `tokenizer` from above)
import colab_eval
import torch

device = next(model.parameters()).device

# Optional: only some tasks
# results = colab_eval.run_benchmark_on_model(TEST_SUITE, model, tokenizer, device, pair_ids=["int_point", "food_values"])

results = colab_eval.run_benchmark_on_model(TEST_SUITE, model, tokenizer, device)
colab_eval.print_report(results)
results
"""

nb["cells"].append(
    {
        "cell_type": "markdown",
        "metadata": {"id": "fabric-test-suite-colab-md"},
        "source": [md],
    }
)
nb["cells"].append(
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"id": "fabric-test-suite-setup"},
        "outputs": [],
        "source": [setup],
    }
)
nb["cells"].append(
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {"id": "fabric-test-suite-benchmark"},
        "outputs": [],
        "source": [bench],
    }
)

p.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("appended 3 cells, total", len(nb["cells"]))
