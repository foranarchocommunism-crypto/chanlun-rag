![缠论RAG：问缠论，也能回到原文核对。](docs/assets/readme-cover.png)

<div align="center">

# 缠论RAG

**让AI查缠论资料，也让你能回到原文核对。**

适用于支持本地工具的AI桌面客户端，例如 **Codex、Claude Desktop、WorkBuddy等等**。<br>
查定义、找条件、核对不同课次的说法，保留出处和未解决的分歧。

[![AI协助安装](https://img.shields.io/badge/开始使用-让AI帮你安装-0f766e)](#让ai帮你安装)
[![Windows x64](https://img.shields.io/badge/Windows-10%20%2F%2011-2563eb)](#开始之前)
[![版本](https://img.shields.io/badge/版本-0.4.2-475569)](https://github.com/foranarchocommunism-crypto/chanlun-rag/releases/tag/v0.4.2)

**[复制安装提示词](#让ai帮你安装)** · **[下载Windows运行包](https://github.com/foranarchocommunism-crypto/chanlun-rag/releases/download/v0.4.2/chanlun-rag-0.4.2-windows-x64.zip)** · **[给Agent的安装指南](INSTALL_FOR_AGENT.md)**

</div>

**导航：** [让AI安装](#让ai帮你安装) · [为什么用RAG](#为什么要使用rag增强检索) · [能做什么](#它能帮你做什么) · [怎么提问](#安装后怎么使用) · [遇到问题](#常见问题) · [手动配置参考](#手动配置参考)

## 让AI帮你安装

先[下载Windows运行包](https://github.com/foranarchocommunism-crypto/chanlun-rag/releases/download/v0.4.2/chanlun-rag-0.4.2-windows-x64.zip)，右键选择“全部解压”。把解压文件夹里的 **INSTALL_FOR_AGENT.md** 拖给你使用的AI，再复制下面整段提示词发送。客户端例如Codex、Claude Desktop、WorkBuddy等等。

```text
我已经下载并解压了“缠论RAG”，请帮我把它连接到我现在使用的AI客户端。

请先读取解压文件夹里的 INSTALL_FOR_AGENT.md，使用我附上的本地文档，不要联网查找安装指南。如果你还不知道解压文件夹的位置，请先让我提供文件夹路径。

你能代办的步骤请直接完成；需要我确认或重启时，一次只告诉我一个动作，说明点哪里、完成后应该看到什么。

连接后，请实际查一次“中枢是什么，成立需要什么条件？”，给出原文出处，并确认这次确实调用了缠论RAG。如果还没有连接成功，请直接说明还差哪一步。
```

安装指南已放在运行压缩包里，读取指南和本地安装不需要上网。有电脑操作权限的Agent可以直接帮你检查和连接；没有这些权限的AI会一步一步带你做。AI客户端自身的在线对话仍按其使用方式联网。

如果AI读不到附件，就把解压文件夹的路径发给它，或将本地指南内容复制给它。解压包内另有 **AI安装提示词.txt**，可以直接打开复制。

## 为什么要使用RAG（增强检索）

你们很可能遇到一个问题：AI看起来侃侃而谈，但实际上说的都是废话，甚至是他瞎编出来的漂亮话。

这就是我们常说的“AI幻觉”。没有参考资料时，大模型可能把不同概念混在一起、遗漏关键条件，甚至编出并不存在的解释。即使不知道答案，它也可能说得十分肯定，让人难以分辨。

RAG则是专门为此而生。可以把RAG直观地理解为给AI配上的资料搜索引擎：先查资料，再依据资料回答。

对于缠论学习，它主要有三个作用：

- **减少“不懂装懂”。** 给AI提供相关原文，并要求它依据资料作答、说明出处。找到依据就解释，依据不足就明确说不确定，减少凭空编造。
- **更精准地定位问题。** 面对“这里为什么不能划成线段”“这个背驰该怎么判断”等问题，先查找相关定义、成立条件和例外，让回答更贴近你真正遇到的难点。
- **让回答更容易核对。** 除了解释，还能给出对应原文和出处。你可以回到资料中检查，判断AI有没有漏掉条件或理解偏差。

**RAG能够减少幻觉、提高回答质量，它让回答更有依据、回答质量大幅提高，让你学习起来更放心、效率更高。**

## 它能帮你做什么

你照常在AI客户端里提问。客户端先从本项目中找资料，再根据找到的资料回答。

| 你想做的事 | 可以这样问 |
| --- | --- |
| 学一个概念 | “中枢是什么，成立需要什么条件？请查缠论RAG并给出处。” |
| 理解联系 | “形态学与动力学如何统一于同一套分析框架？” |
| 逻辑推导 | “走势必完美如何推导出可操作的结构定理？” |
| 关系界定 | “级别递归于区间套的区别与联系是什么？” |
| 细节难点 | “线段如何划分？具体规则如何理解？”<br>• “某处背驰到底该怎么判断”<br>• “走势多义性，那这里到底怎么划分？” |
| 分析实际案例 | “【截图这里】这段走势应该怎么分析？请结合图中结构，核对成立条件，并给出原文依据。” |
| 对照不同课次 | “第18课和第54课关于中枢连接级别的表述有什么不同？请保留分歧。” |
| 核对AI的说法 | “请给出支持这个解释的原文、PDF文件名和PDF页码。” |

例如，查询中枢成立条件时，本地检索能找到“至少三个连续次级别走势类型所重叠的部分”的定义，并可继续核对相关条件。原文位置包括上册 `volume_1.pdf` 的 **PDF第76页、第82页**。

资料来自随包提供的两册固定PDF。默认采用本项目已经复核的条目；有争议的解释保留争议。知识库现已固定，后续不安排新增资料。

**使用边界： 本项目提供查证材料，最终回答由AI客户端组织。它不能保证AI每句话都正确，也不提供行情、自动交易或收益承诺。**

## 开始之前

| 需要准备 | 说明 |
| --- | --- |
| Windows电脑 | Windows 10 1809及以后版本或Windows 11，**x64**；本运行包不支持Mac、32位或Windows ARM64 |
| 一个AI桌面客户端 | 例如Codex、Claude Desktop、WorkBuddy等等，任选支持本地工具的客户端，登录自己的账号 |
| 磁盘空间 | 下载约500MB，解压约1GB；建议至少留出3GB用于下载和解压 |
| 网络 | 下载、客户端登录和在线回答通常需要网络；本项目的知识检索在电脑本地完成 |

运行包已带好所需组件，**无需另装Node.js、Python、Docker或虚拟机，也不需要为本项目申请API密钥**。AI客户端自己的使用条件和费用以其官方说明为准。客户端可能把取到的引文发给其模型，因此“本地检索”不代表整段对话离线。

## 安装后怎么使用

AI确认连接成功后，新开一段对话，试着发送：

> 请查缠论RAG，解释中枢是什么、成立需要什么条件，并给出原文出处。

正常时，AI会实际调用资料库，再根据查到的内容回答，并给出PDF文件名和页码。若只有一段回答、没有查资料的记录，可以继续说：

> 请确认这次确实调用了缠论RAG，并读取对应原文给我核对；如果没有调用成功，请直接说明。

以后提问时加上“**请查缠论RAG，并给出原文出处**”即可。遇到歧义或待核提示，让AI分别说明来源。

## 常见问题

| 你遇到的情况 | 可以这样处理 |
| --- | --- |
| AI说不能操作这台电脑 | 告诉它：“请按安装指南一步一步带我做，一次只说一个动作。” |
| AI读不到本地指南 | 把解压文件夹路径发给AI，或把本地INSTALL_FOR_AGENT.md的内容复制给它 |
| AI只说配置已保存 | 告诉它：“请继续检查连接，并实际查一次原文，确认能用了再告诉我。” |
| 重启后不知道怎么继续 | 告诉它：“我已重启，请读取刚才保存的安装进度，继续检查缠论RAG。” |
| 换了文件夹后不能使用 | 告诉它：“资料位置变了，请更新连接位置并重新试查。” |

分析实际案例时，把图表截图附在提问旁边即可。详细说明见[开始使用](开始使用.md)。如果自己下载文件，选择Release中的 **Windows运行ZIP**；GitHub绿色Code按钮里的Download ZIP和Source code是开发资料。

<details>
<summary><strong>开发者与资料核对</strong></summary>

公开代码仓库保留源码、两册PDF、知识底本、审校材料、研究记录及发布验收证据，供追溯与维护使用。用户运行包不包含完整开发审校档案。

| 目录或文件 | 内容 |
| --- | --- |
| `INSTALL_FOR_AGENT.md` | 指导Agent帮助用户下载、校验、连接并实际试查 |
| `source/` | 当前源码、测试、构建脚本及 `curation/` 审校材料 |
| `shared-knowledge/v0.1.0/` | 固定知识底本、PDF与来源记录 |
| `docs/development-history/` | 历史计划与审查报告；历史目标不代表当前承诺 |
| `research-artifacts/`、`validation-runs/` | 研究材料与实际运行证据 |
| `验收记录/` | 发布验证、资料保留核对与验证边界 |

开发历史保存在 `archive/development-main` 分支。模型、依赖和运行时通过Release运行包提供。维护参见[固定版本说明](https://github.com/foranarchocommunism-crypto/chanlun-rag/blob/main/source/docs/fixed-release.md)和[资料保留说明](https://github.com/foranarchocommunism-crypto/chanlun-rag/blob/main/docs/资料保留说明.md)。

运行包及连接助手已有测试记录；各客户端逐一登录后的完整界面验收、全新Windows系统验收仍未完成，详见[验证记录](https://github.com/foranarchocommunism-crypto/chanlun-rag/blob/main/验收记录/入门发布验证.md)。

</details>

## 手动配置参考

如果希望自己操作，可从下面的详细教程开始。**以下以Codex、Claude Desktop、WorkBuddy等等为例**，其他支持本地工具的客户端可让AI参照其实际设置完成连接。

| 客户端示例 | 详细步骤 |
| --- | --- |
| 下载、解压与本机检查 | [打开手动安装步骤](开始使用.md#下载与检查) |
| Codex桌面端 | [打开Codex示例](开始使用.md#codex桌面端) |
| Claude Desktop | [打开Claude示例](开始使用.md#claude-desktop) |
| WorkBuddy | [打开WorkBuddy示例](开始使用.md#workbuddy) |
| 其他客户端等等 | [交给Agent按客户端实际配置连接](INSTALL_FOR_AGENT.md#其他客户端) |

界面入口参考 [OpenAI官方MCP文档](https://learn.chatgpt.com/docs/extend/mcp)、[Claude本地连接教程](https://modelcontextprotocol.io/docs/2026-07-28/develop/connect-local-servers)、[WorkBuddy官方MCP文档](https://www.codebuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/MCP-Guide)。`MCP`是客户端里连接本地工具的功能名称，具体操作见上面的手动教程。
