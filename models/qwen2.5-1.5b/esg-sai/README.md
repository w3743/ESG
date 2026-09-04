# ESG SAI adapter

这是 B-SAI 任务的 QLoRA 适配器，目标是判断一条已经确认属于 ESG 的陈述是否为 NonSpecific。

输出必须是严格 JSON：

```json
{"non_specific":0}
```

其中 `0` 表示 Specific，`1` 表示 NonSpecific；Ambiguous 和 Generic 均映射为 `1`。完整的底座模型、加载方式和限制请参见上级目录的 README。
