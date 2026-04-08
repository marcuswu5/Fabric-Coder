"""
Colab/local driver: inject model-generated Java into test_suite and run Gradle + JUnit.

Depends: PyYAML (pip). On Colab, install JDK 17 and chmod +x gradlew (see prepare_runtime).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Optional

try:
    import yaml
except ImportError as e:
    yaml = None  # type: ignore
    _YAML_ERR = e
else:
    _YAML_ERR = None


def _require_yaml() -> None:
    if yaml is None:
        raise ImportError(
            "PyYAML is required: pip install pyyaml"
        ) from _YAML_ERR


def default_test_suite_root() -> Path:
    env = os.environ.get("TEST_SUITE_ROOT")
    if env:
        return Path(env).resolve()
    here = Path(__file__).resolve().parent
    return here


def prepare_runtime(test_suite_root: Optional[Path] = None) -> Path:
    """
    Ensure gradlew is executable (Linux/Colab) and JAVA_HOME points at JDK 17+ if discoverable.
    """
    root = Path(test_suite_root or default_test_suite_root()).resolve()
    gradlew = root / "gradlew"
    if gradlew.is_file():
        mode = gradlew.stat().st_mode
        gradlew.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    java_home = os.environ.get("JAVA_HOME")
    if not java_home or not Path(java_home).is_dir():
        for candidate in (
            "/usr/lib/jvm/java-17-openjdk-amd64",
            "/usr/lib/jvm/java-21-openjdk-amd64",
        ):
            if Path(candidate).is_dir():
                os.environ["JAVA_HOME"] = candidate
                path = os.environ.get("PATH", "")
                os.environ["PATH"] = f"{candidate}/bin:{path}"
                break
    return root


def install_colab_java() -> None:
    """Non-fatal on local machines; on Colab installs openjdk-17-jdk via apt."""
    if shutil.which("java"):
        return
    try:
        subprocess.run(
            ["apt-get", "update", "-qq"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        subprocess.run(
            ["apt-get", "install", "-y", "-qq", "openjdk-17-jdk"],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
        jdk = Path("/usr/lib/jvm/java-17-openjdk-amd64")
        if jdk.is_dir():
            os.environ["JAVA_HOME"] = str(jdk)
            os.environ["PATH"] = f"{jdk}/bin:{os.environ.get('PATH', '')}"
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(
            "Could not apt-get install Java; install JDK 17 manually and set JAVA_HOME.",
            file=sys.stderr,
        )


def load_pair_file(pair_path: Path) -> dict[str, Any]:
    _require_yaml()
    text = pair_path.read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"Invalid pair YAML: {pair_path}")
    return data


def load_pairs_from_manifest(test_suite_root: Path) -> list[dict[str, Any]]:
    _require_yaml()
    manifest_path = test_suite_root / "pairs" / "manifest.yaml"
    raw = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    names = (raw or {}).get("pairs") or []
    out: list[dict[str, Any]] = []
    for name in names:
        p = test_suite_root / "pairs" / str(name)
        d = load_pair_file(p)
        d["_pair_file"] = str(p.relative_to(test_suite_root))
        out.append(d)
    return out


def extract_java_from_completion(text: str) -> Optional[str]:
    """
    Take the first fenced Java block, or first generic ``` block if language not specified.
    """
    if not text or not text.strip():
        return None
    patterns = [
        re.compile(r"```(?:java)\s*\n(.*?)```", re.DOTALL | re.IGNORECASE),
        re.compile(r"```\s*\n(.*?)```", re.DOTALL),
    ]
    for pat in patterns:
        m = pat.search(text)
        if m:
            body = m.group(1).strip()
            if body:
                return body
    if "package " in text or "public class " in text or "public final class " in text:
        return text.strip()
    return None


def inject_primary_file(test_suite_root: Path, pair: dict[str, Any], java_source: str) -> Path:
    rel = pair["target"]["primary_file"]
    path = test_suite_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(java_source, encoding="utf-8")
    return path


def run_gradle_test(
    test_suite_root: Path,
    test_class: str,
    timeout_sec: int = 300,
) -> subprocess.CompletedProcess[str]:
    gradlew = test_suite_root / "gradlew"
    cmd = [
        str(gradlew),
        "test",
        "--no-daemon",
        "-q",
        f"--tests={test_class}",
    ]
    env = os.environ.copy()
    return subprocess.run(
        cmd,
        cwd=str(test_suite_root),
        capture_output=True,
        text=True,
        timeout=timeout_sec,
        env=env,
    )


def read_file(test_suite_root: Path, rel: str) -> str:
    return (test_suite_root / rel).read_text(encoding="utf-8")


def evaluate_completion(
    test_suite_root: Path,
    pair: dict[str, Any],
    completion_text: str,
    restore_after: bool = True,
) -> dict[str, Any]:
    """
    Parse Java from model output, write primary_file, run the pair's JUnit class, optionally restore file.
    """
    root = Path(test_suite_root).resolve()
    rel = pair["target"]["primary_file"]
    original = read_file(root, rel)
    err: Optional[str] = None
    java = extract_java_from_completion(completion_text)
    if java is None:
        err = "no_java_fence"
        return {
            "pair_id": pair.get("id"),
            "ok": False,
            "error": err,
            "raw_completion": completion_text[:8000],
        }
    inject_primary_file(root, pair, java)
    test_class = pair["verifier"]["test_class"]
    try:
        proc = run_gradle_test(root, test_class)
    except subprocess.TimeoutExpired as te:
        if restore_after:
            inject_primary_file(root, pair, original)
        return {
            "pair_id": pair.get("id"),
            "ok": False,
            "error": "timeout",
            "stderr": (te.stderr or "")[:8000] if isinstance(te.stderr, str) else "",
        }
    ok = proc.returncode == 0
    result = {
        "pair_id": pair.get("id"),
        "ok": ok,
        "returncode": proc.returncode,
        "stdout": (proc.stdout or "")[-12000:],
        "stderr": (proc.stderr or "")[-12000:],
        "extracted_java_chars": len(java),
    }
    if restore_after:
        inject_primary_file(root, pair, original)
    return result


def generate_completion_hf(
    model: Any,
    tokenizer: Any,
    prompt: str,
    device: Any,
    max_new_tokens: int = 2048,
    system_message: Optional[str] = None,
) -> str:
    """Use transformers causal LM; applies chat template when available."""
    import torch

    messages: list[dict[str, str]] = []
    if system_message:
        messages.append({"role": "system", "content": system_message})
    messages.append({"role": "user", "content": prompt})

    if getattr(tokenizer, "chat_template", None):
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    else:
        text = prompt

    inputs = tokenizer(text, return_tensors="pt").to(device)
    with torch.inference_mode():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            pad_token_id=getattr(tokenizer, "pad_token_id", None)
            or getattr(tokenizer, "eos_token_id", None),
        )
    in_len = inputs["input_ids"].shape[1]
    gen_ids = out[0, in_len:]
    return tokenizer.decode(gen_ids, skip_special_tokens=True)


def run_benchmark_on_model(
    test_suite_root: Optional[Path],
    model: Any,
    tokenizer: Any,
    device: Any,
    pair_ids: Optional[list[str]] = None,
    max_new_tokens: int = 2048,
    system_message: Optional[str] = None,
    generator: Optional[Callable[..., str]] = None,
) -> list[dict[str, Any]]:
    """
    For each YAML pair, generate with the given model and run Gradle tests.

    Override `generator(prompt) -> str` to use a custom inference path.
    """
    root = Path(test_suite_root or default_test_suite_root()).resolve()
    prepare_runtime(root)
    pairs = load_pairs_from_manifest(root)
    if pair_ids is not None:
        want = set(pair_ids)
        pairs = [p for p in pairs if p.get("id") in want]

    results: list[dict[str, Any]] = []
    gen_fn = generator
    for pair in pairs:
        prompt = pair.get("prompt") or ""
        if gen_fn is not None:
            completion = gen_fn(prompt)
        else:
            completion = generate_completion_hf(
                model,
                tokenizer,
                prompt,
                device,
                max_new_tokens=max_new_tokens,
                system_message=system_message,
            )
        ev = evaluate_completion(root, pair, completion, restore_after=True)
        ev["raw_completion"] = completion[:12000]
        results.append(ev)
    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(results)
    passed = sum(1 for r in results if r.get("ok"))
    return {
        "total": n,
        "passed": passed,
        "pass_rate": (passed / n) if n else 0.0,
        "by_id": {r.get("pair_id"): r.get("ok") for r in results},
    }


def print_report(results: list[dict[str, Any]]) -> None:
    print(json.dumps(summarize(results), indent=2))
    for r in results:
        if not r.get("ok"):
            print(f"\n--- failed: {r.get('pair_id')} ({r.get('error') or 'tests'}) ---")
            if r.get("stderr"):
                print(r["stderr"][-4000:])
