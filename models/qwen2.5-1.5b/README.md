# Qwen2.5-1.5B ESG LoRA adapters

这两个目录是基于 `Qwen/Qwen2.5-1.5B-Instruct` 训练的独立 PEFT/LoRA 适配器。使用时需要同时加载基础模型和其中一个适配器。

| 适配器 | 用途 | 输出契约 |
| --- | --- | --- |
| `esg-split` | A：企业报告段落拆分 | `{"statements":["..."]}` |
| `esg-sai` | B-SAI：ESG 陈述具体性判断 | `{"non_specific":0}` 或 `{"non_specific":1}` |

推荐通过 Qwen 的 chat template 构造输入：先发送 `system` 消息，再发送一条 `user` 消息。应用层应解析 JSON，并拒绝额外说明文字。

基本加载方式：

```python
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

base_id = "Qwen/Qwen2.5-1.5B-Instruct"
adapter_dir = "models/qwen2.5-1.5b/esg-split"  # 或 esg-sai

tokenizer = AutoTokenizer.from_pretrained(base_id)
model = AutoModelForCausalLM.from_pretrained(
    base_id, torch_dtype="auto", device_map="auto"
)
model = PeftModel.from_pretrained(model, adapter_dir)
```

A 模型的 `system` 内容和 B-SAI 模型的 `system` 内容已保存在各自训练数据中；完整示例和字段定义见仓库根目录说明及 `training/datasets/`。

本次训练采用四批次去重后的数据。A 的验证集 loss 为 0.0693，B-SAI 的验证集 loss 为 0.0526；这些数值是训练期间的验证指标，不等同于独立测试集的最终业务验收结果。
