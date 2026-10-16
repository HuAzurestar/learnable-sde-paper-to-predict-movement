# 论文入口

**PIRC-17 只以下面的当前稿为准。** 不需要在 revision、review 或 reader 版本中挑选。

本期作为探索性实验结项；当前稿含实现别名与5分钟排序敏感性的审查修正。
原科学限制保留，不认证正式投稿条件或模型的一般优越性。

| 语言 | 正文 | 科学补充材料 |
| --- | --- | --- |
| 中文 | [阅读正文](pirc17/current/zh/main.pdf) | [补充材料：17图、50表](pirc17/current/zh/supplement.pdf) |
| English | [Main paper](pirc17/current/en/main.pdf) | [Scientific supplement](pirc17/current/en/supplement.pdf) |

修改源码：[中文 main.tex](pirc17/zh/main.tex)、[英文 main.tex](pirc17/en/main.tex)。
每种语言的 `supplement.tex` 是补充材料入口，`audit-notes.tex` 是独立审查记录入口。

当前稿的[构建记录](pirc17/current/build-manifest.json)保留原始来源与哈希。
[中文审查记录](pirc17/current/zh/audit-notes.pdf)／[English audit](pirc17/current/en/audit-notes.pdf)
仅供追溯，不是另一版论文。

[历史归档](pirc17/archive/README.md)集中保存旧稿、旧交付和审查记录；均不作为当前稿。
数据、图片、数值证据和现行编译／重建模板保持原位置、原内容。

重编译当前六份文档：

```console
python scripts/build_pirc17_revision46.py --output-dir <新的外部构建目录>
```

`paper/en`、`paper/zh` 属于另一条历史研究稿件，不是 PIRC-17 的当前入口。
