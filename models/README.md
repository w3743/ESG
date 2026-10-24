# 模型目录

| 模型 | 形式 | 用途与状态 | 获取方式 |
| --- | --- | --- | --- |
| [Qwen3.5-9B B09 · 2026-09-29](qwen3.5-9b/esg-split-classify-b09-20260929/README.md) | 合并权重 GGUF，Q5_K_M | ESG 拆分与分类，实验候选 | GitHub 预发布版分卷；附校验与合并工具 |
| [Qwen2.5-1.5B ESG Split](qwen2.5-1.5b/esg-split/README.md) | LoRA 适配器 | 历史版本，段落拆分 | Git LFS；需要对应基础模型 |
| [Qwen2.5-1.5B ESG SAI](qwen2.5-1.5b/esg-sai/README.md) | LoRA 适配器 | 历史版本，具体性二分类 | Git LFS；需要对应基础模型 |
| `esg-bert-classifier-gold3x-20260824.zip` | 历史模型包 | 旧版 BERT 分类器归档，运行元数据见包内文件 | 根模型目录的 Git LFS 文件 |

大权重与模型包使用 Git LFS，超过单文件分发限制的模型使用 GitHub Release 分卷。README、配置、分词器和下载清单均作为普通 Git 文件保存。

获取历史 LFS 权重：

```sh
git lfs install
git lfs pull --include="models/qwen2.5-1.5b/**/adapter_model.safetensors"
```

新模型按 `models/<base-family>/<task-and-version>/` 保存最小运行元数据。公开交付不包含训练集、训练脚本、训练状态、日志或本地环境路径。基础模型及历史模型包的使用应遵守各自许可；本仓库未新增对它们的许可授权。
