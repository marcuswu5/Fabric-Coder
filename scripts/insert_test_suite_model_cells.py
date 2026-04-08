"""Insert test_suite model+tokenizer load cells before the benchmark cell."""
import json
from pathlib import Path

p = Path(__file__).resolve().parent.parent / "FineTuning.ipynb"
nb = json.load(p.open(encoding="utf-8"))

if any(c.get("metadata", {}).get("id") == "fabric-test-suite-load-model" for c in nb["cells"]):
    print("fabric-test-suite-load-model cell already present; skipping")
    raise SystemExit(0)

insert_at = None
for i, c in enumerate(nb["cells"]):
    if c.get("metadata", {}).get("id") == "fabric-test-suite-benchmark":
        insert_at = i
        break
if insert_at is None:
    raise SystemExit("fabric-test-suite-benchmark cell not found")

md = {
    "cell_type": "markdown",
    "metadata": {"id": "fabric-test-suite-load-md"},
    "source": [
        "### test_suite: load model and tokenizer\n",
        "\n",
        "Run after **Setup**. Uses `BASE_MODEL` from **Global Variables** when defined; otherwise `deepseek-ai/deepseek-coder-6.7b-instruct`. "
        "4-bit on GPU, float32 on CPU.\n",
        "\n",
        "To evaluate a **LoRA adapter**, uncomment the `PeftModel` lines and set `TEST_SUITE_ADAPTER_DIR`.\n",
    ],
}

code = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {"id": "fabric-test-suite-load-model"},
    "outputs": [],
    "source": [
        "# test_suite: load tokenizer + causal LM for benchmark generations\n",
        "import torch\n",
        "from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig\n",
        "\n",
        'TEST_SUITE_MODEL_ID = globals().get("BASE_MODEL", "deepseek-ai/deepseek-coder-6.7b-instruct")\n',
        "# Optional: path to a saved LoRA adapter (uncomment PeftModel lines below)\n",
        'TEST_SUITE_ADAPTER_DIR = None  # e.g. Path("/content/my-lora-adapter")\n',
        "\n",
        "tokenizer = AutoTokenizer.from_pretrained(TEST_SUITE_MODEL_ID, trust_remote_code=True)\n",
        "if getattr(tokenizer, \"pad_token\", None) is None:\n",
        "    tokenizer.pad_token = tokenizer.eos_token\n",
        "\n",
        "if torch.cuda.is_available():\n",
        "    quant_config = BitsAndBytesConfig(\n",
        "        load_in_4bit=True,\n",
        "        bnb_4bit_quant_type=\"nf4\",\n",
        "        bnb_4bit_compute_dtype=torch.float16,\n",
        "        bnb_4bit_use_double_quant=True,\n",
        "    )\n",
        "    model = AutoModelForCausalLM.from_pretrained(\n",
        "        TEST_SUITE_MODEL_ID,\n",
        "        quantization_config=quant_config,\n",
        "        device_map=\"auto\",\n",
        "        trust_remote_code=True,\n",
        "    )\n",
        "else:\n",
        "    model = AutoModelForCausalLM.from_pretrained(\n",
        "        TEST_SUITE_MODEL_ID,\n",
        "        torch_dtype=torch.float32,\n",
        "        trust_remote_code=True,\n",
        "    )\n",
        "\n",
        "# if TEST_SUITE_ADAPTER_DIR:\n",
        "#     from peft import PeftModel\n",
        "#     model = PeftModel.from_pretrained(model, str(TEST_SUITE_ADAPTER_DIR))\n",
        "\n",
        "model.eval()\n",
        'print("test_suite model:", TEST_SUITE_MODEL_ID, "| cuda:", torch.cuda.is_available())\n',
    ],
}

nb["cells"][insert_at:insert_at] = [md, code]

for c in nb["cells"]:
    if c.get("metadata", {}).get("id") == "fabric-test-suite-benchmark":
        src = c.get("source", [])
        if src and isinstance(src[0], str) and src[0].startswith("# test_suite: run JUnit"):
            src[0] = (
                "# test_suite: run JUnit checks (run load model + tokenizer cell above first)\n"
            )
        break

for c in nb["cells"]:
    if c.get("metadata", {}).get("id") == "fabric-test-suite-colab-md":
        c["source"] = [
            "# test_suite: Colab Java benchmark\n",
            "\n",
            "Run **Setup**, then **load model and tokenizer**, then **Benchmark**.\n",
            "\n",
            "Set `REPO_ROOT` / clone so `test_suite/` exists (see **Global Variables** for `BASE_MODEL`).\n",
        ]
        break

p.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
print("inserted load cells at index", insert_at)
