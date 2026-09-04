# ESG 仓库上传约束与命名规范

## 1. 仓库白名单

允许提交的路径只有：

- models/**
- pdf_text/**
- 根目录的 README.md、UPLOAD_CONSTRAINTS.md、.gitattributes、.gitignore

禁止提交：

- 任意原始 PDF：*.pdf、*_origin.pdf
- pdf_text/ 中的图片和版面中间产物：*.png、*.jpg、*.jpeg、*.webp、*_layout.pdf、*_span.pdf
- pdf_text/ 中的 7z/zip/tar 等整包归档；模型目录内只有在模型 README 明确说明、且有校验值的模型打包文件才可保留
- 训练集、训练脚本、缓存、日志、临时目录和本地环境文件
- 任何根目录下新增的业务文件或业务目录

## 2. 文字结果结构

每份报告必须使用以下结构：

pdf_text/batch-<NN>/<ticker>/
  report.md
  manifest.json

其中：

- <NN> 为两位批次号，例如 04、05、06、07。
- <ticker> 使用证券代码和市场后缀，例如 600000.SH、000001.SZ、0700.HK。
- 目录名直接使用证券代码，保留市场后缀和点号；不使用公司简称、下载时间或随机字符串。
- 固定文件名用于自动校验；不得用下载时间、随机 UUID 或 final2 等临时后缀。
- 批次清单统一放在 pdf_text/manifests/batch-<NN>.tsv。

## 3. 内容准入

每份报告进入仓库前必须满足：

1. 证券代码和公司主体在目标批次内唯一，且与已发布批次交叉去重。
2. 来源 URL、下载时间、报告年份、报告标题、PDF SHA-256 和规范化文本指纹记录在清单中。
3. 正文确认是目标年份的 ESG、可持续发展或社会责任报告。
4. report.md 和 manifest.json 非空；manifest.json 可解析；核心文件不得为零字节。
5. 解析失败、空文本、年份不符、重复报告或无法验证来源的报告不得提交，必须修复或替换。
6. pdf_text/ 中不得出现任何 PDF 或图片文件；解析结果不得夹带原始文件副本。

## 4. MinerU 解析规范

标准流程：

mineru -p <pdf> -o <output> -b pipeline -m txt -l ch -t false

仅当 Markdown 为空或报告为扫描型时，单独使用 OCR 重跑：

mineru -p <pdf> -o <output> -b pipeline -m ocr -l ch -t false

验收时只复制文字交付物（Markdown 和来源清单），不要复制原始 PDF、MinerU 结构 JSON、图片、版面 PDF 或模型缓存。

## 5. Git/LFS 发布流程

1. git fetch origin main，在最新远程 main 上建立隔离发布工作树。
2. 运行文件扩展名、目录白名单、Markdown 非空、来源 manifest JSON 解析和清单唯一性检查。
3. 只按明确路径 git add models/... pdf_text/... README.md UPLOAD_CONSTRAINTS.md .gitattributes .gitignore，禁止 git add .。
4. 检查 git diff --cached --name-only，确认没有 PDF、图片、归档、训练文件或临时文件。
5. 模型文件继续使用 Git LFS；解析文字保持普通 Git 文件，避免小文件 LFS 对象泛滥。
6. 使用清晰提交信息，例如 Add batch 05 parsed PDF text 或 Update model release。
7. 先推送 LFS 对象，再快进推送 main；禁止 --force。
8. 推送后核对远程提交、LFS 指针、远程文件树和本地 git status。

## 6. 发布前硬性检查

git diff --cached --name-only
git diff --cached --check
git lfs status
git ls-tree -r --name-only HEAD

验收必须证明：

- 暂存路径全部属于白名单；
- pdf_text/ 内 PDF、图片和归档数量为 0；仓库中不存在训练集、训练脚本或缓存；
- 每个批次的报告数、公司数、代码数和文本指纹数符合清单；
- Markdown 和来源 manifest 核心输出全部有效；
- GitHub 远程 main 与本次发布提交一致；
- LFS 指针的 OID 与本地文件 SHA-256 一致。
