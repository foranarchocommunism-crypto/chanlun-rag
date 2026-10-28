# 离线评测工具留存

这是实际使用的现有评测工具源码副本，原文件未修改；不含新应用或Node运行时。evaluation内是冻结的240道模型复核开发题，保留原有图谱版本和金标准。需Python标准库及Node 24或以上复算。

以交付知识库目录为KB_PATH，从本目录执行：

```powershell
python scripts/snapshot-retrieval-eval.py --kb KB_PATH --max-batch 25 --output NEW_EMPTY_SNAPSHOT
node scripts/evaluate-retrieval-baselines.mjs NEW_EMPTY_SNAPSHOT NEW_REPORT.json
```

必须使用新的快照/结果路径；不要覆盖原题或正式知识库。新快照的物理SQLite哈希可能随备份而改变，仍须确认graph_version相同。原运行的自然问题输入/候选预算/评价单位、实际结果和限制在audit报告中，不能把离线融合结果当现有搜索产品能力。
