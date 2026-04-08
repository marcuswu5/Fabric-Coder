import json
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "FineTuning.ipynb"
nb = json.load(p.open(encoding="utf-8"))
for c in nb["cells"]:
    if c.get("metadata", {}).get("id") == "fabric-test-suite-colab-md":
        c["source"] = [
            "## test_suite: Colab Java benchmark\n",
            "\n",
            "Run **Setup** once per Colab runtime after you have this repo on the VM (clone or Drive). "
            "Then load your model as usual and run **Benchmark** — it uses `model` and `tokenizer` from earlier cells "
            "(device is taken from the model).\n",
            "\n",
            "Set `REPO_ROOT` to the folder that contains `test_suite/` (default `/content/Fabric-Coder`).\n",
        ]
        break
else:
    raise SystemExit("markdown cell not found")
for c in nb["cells"]:
    if c.get("metadata", {}).get("id") == "fabric-test-suite-benchmark":
        c["source"] = [
            "# test_suite: run JUnit checks on model completions (expects `model` and `tokenizer` from above)\n",
            "import colab_eval\n",
            "import torch\n",
            "\n",
            "device = next(model.parameters()).device\n",
            "\n",
            "# Optional: only some tasks\n",
            '# results = colab_eval.run_benchmark_on_model(TEST_SUITE, model, tokenizer, device, pair_ids=["int_point", "food_values"])\n',
            "\n",
            "results = colab_eval.run_benchmark_on_model(TEST_SUITE, model, tokenizer, device)\n",
            "colab_eval.print_report(results)\n",
            "results\n",
        ]
        break
else:
    raise SystemExit("cell not found")
p.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("patched test_suite Colab cells")
