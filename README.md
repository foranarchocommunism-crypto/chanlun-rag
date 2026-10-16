# 缠中说禅 Agent 知识访问包

独立于人类桌面应用的本地查询工具。两端只读访问同一份共享 SQLite 图谱，复用本仓库的 `src/core.mjs`。结构化检索用于原文研究、概念解释与证据核查。

## 使用

需要 Node 24 或交付包中附带的运行时。图谱包目录通过 `--kb` 或 `CHAN_KG_PATH` 指定。

```powershell
node bin/chan-kg.mjs search 中枢 --kb ..\shared-knowledge\v0.1.0
node bin/chan-kg.mjs concept 走势中枢 --kb ..\shared-knowledge\v0.1.0
node bin/chan-kg.mjs search 级别 --scope source --kb ..\shared-knowledge\v0.1.0
node bin/chan-kg.mjs coverage --kb ..\shared-knowledge\v0.1.0
```

Agent 开始研究前读取 [取证步骤](AGENT_GUIDE.md)。机器可读接口以 JSON 返回版本、命题身份、适用条件、复核状态和证据；诊断信息输出至 stderr。

知识检索匹配命题正文、适用条件和例外。这些字段直接命中时排在仅通过概念关联命中的结果之前，默认仍只返回已复核知识。

## 图谱构建

固定来源为用户提供的 `volume_1.pdf` 与 `volume_2.pdf`。`tools/extract_corpus.py` 建立全文、字符坐标、发言者切分、配图位置和待核候选。语义复核由后续构建批次完成，不以词汇命中替代复核。共享图谱与原始 PDF 位于独立数据目录，不提交到代码仓库。

数据契约见 [schema.sql](contracts/schema.sql)。`explicit/inferred` 与 `pending/reviewed/rejected` 独立记录；“已复核”不代表所有解释歧义已经消除。

整理批次的字段契约见 [curation.schema.json](contracts/curation.schema.json)。`python tools/import_curation.py --kb <图谱目录> --check <批次.jsonl>` 只读预检引用、身份、字符映射、坐标、关系和推论前提；机器通过不替代原文语义或原图复核。正式导入前备份共享数据库和清单。新增记录填写实际复核者；作者解盘技术解释在 `review_note` 中分别写明“语境：”和“适用条件：”。

阶段进度与恢复入口见 [curation/progress.json](curation/progress.json)。覆盖日志采用追加记录；按课程读取最新记录，并核对其批次是否已导入。旧批003的第65、66课条目由新批005重新复核，第67课条目由新批004重新复核；旧批保留历史，不整文件重复导入。

## 详细覆盖与重要性

逐课提取定义、定理、判定条件、前置关系、例外、辨析、作者技术答疑及相关案例。每课分别记录审读进度、抽取进度、排除理由和待核问题。重要性由整理者评定并附理由：1基础核心、2主要方法、3补充深化、4背景细节。关键条件和例外跟随其核心命题，所有等级默认保留。使用 `--max-importance 1` 可只看基础核心。

## 构建与交付

`npm test` 在真实共享图谱上检查固定来源、中文查询、完整条件、作者身份、精确引文坐标、推论前提、重要性和CLI独立性。`npm run validate` 检查所有默认知识；`npm run export` 从同一图谱生成JSONL/Markdown。

`npm run package -- --node <node.exe>` 输出带Node运行时的独立Agent访问包。共享图谱是相邻独立目录，两端通过同一路径读取。构建工具及审读记录保存在源仓库，日常使用无需运行PDF抽取器或支付模型API费用。
