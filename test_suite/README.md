# test_suite

## Requirements

- **JDK 17** (or newer)

## Run tests

From this directory:

**Windows**

```bat
gradlew.bat test
```

**Linux / macOS**

```bash
chmod +x gradlew
./gradlew test
```

Gradle downloads itself on first run. All tests should pass with the checked-in sources.

## Colab (`FineTuning.ipynb`)

Use the **test_suite** cells at the end of the notebook: **Setup** → **load model and tokenizer** → **Benchmark**.
