# Training scripts

`clean_four_batches_20260903.py` reproduces the four-batch deduplication and split logic. For a checkout different from the original Windows workspace, set these environment variables before running it:

```powershell
$env:ESG_WORKSPACE = "C:\path\to\workspace"
$env:ESG_FORMAL_DATA_ROOT = "C:\path\to\formal-training-data"
$env:ESG_CLEAN_OUTPUT = "C:\path\to\cleaned-output"
python training/scripts/clean_four_batches_20260903.py
```

`run_qwen25_15b_four_batches.ps1` is the sequential A-then-B runner used for the Qwen2.5-1.5B experiments. It requires explicit paths for the LLaMA-Factory CLI, configs, outputs, logs, and status file.
