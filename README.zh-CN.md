# CodeAccord

**先就变更达成一致，再完成实现。**

CodeAccord 是一个轻量、可移植、以规格驱动软件变更的 Agent Skill，统一处理产品需求、Bug 修复、重构、配置调整和其他代码库工作：

```text
探索 [调查 <-> 质疑] -> 确认 -> 实施 -> 验证
```

Agent 会在不修改产品文件的前提下，反复调查真实项目并检验用户和自己的假设。证据和决策收敛后，它会输出一份格式固定、可以快速审查的 Accord，取得一次明确确认，再完成实施和验证。

[English](README.md)

## 为什么需要 CodeAccord

编码 Agent 容易走向两个极端：问题尚未查清就开始修改，或者给日常工作套上过重的规划流程。CodeAccord 保留规格驱动开发中真正有用的边界，同时控制流程成本：

- 只有一个 Skill；
- 只有一个方案确认点；
- 核心流程不需要 CLI 或运行时依赖；
- 对话始终是主要工作界面；
- 最多只有一份临时恢复 checkpoint；
- 不累积 change 文件，也没有同步和归档流程。

用户决定想得到的产品结果，Agent 仍必须根据源码、测试、日志、契约和项目约束判断用户提出的原因和实现方案是否成立。

## 工作流

| 阶段 | 作用 |
| --- | --- |
| 探索 | 在调查和质疑之间循环，回答问题并收敛证据和推荐方案，不修改产品文件。 |
| 确认 | 明确变更范围和验收标准，取得一次明确确认。 |
| 实施 | 完成已确认的代码、测试和必要文档。 |
| 验证 | 对照确认内容检查结果并报告证据。 |

CodeAccord 在同一套工作流中识别产品需求、Bug 和混合变更。用户不需要反复强调“先分析”或“暂时不要改代码”。

## 固定的 Accord

Explore 仍在讨论方向时只输出简短的发现和建议。即使 Agent 认为证据已经充分，也不能自行结束 Explore。用户认可方向或要求整理完整方案后，CodeAccord 才输出一次完整结构：实施就绪状态、变更类型、目标、当前事实、实施方案、修改范围、兼容性与风险、验收标准和开放决策。小改动也保留这些标题，但每节可以只有一句。

`确认后可实施` 表示用户确认后可以直接开始修改；`已预授权` 表示用户已经要求直接实施；`仍有决策阻塞` 必须列出剩余选择，不能作为完整实施范围请求确认。

首次 Accord 之后发生方案变化时，只输出 `Accord 变更`，包含原决定、新决定、影响范围、验收变化和开放决策，不重复未变化章节。已确认的变更合并进恢复 checkpoint，待确认变更保留在 `Unresolved`。只有用户明确要求或无法恢复原基准时，才重新输出完整 Accord。

## 安装

### 用 npx 安装

[`skills`](https://github.com/vercel-labs/skills) 命令行工具会把 CodeAccord 安装到本机检测到的各个 Agent 的 Skill 目录，并在 lock 文件中记录来源：

```bash
npx skills add 6xdax/CodeAccord      # 安装到当前项目
npx skills add -g 6xdax/CodeAccord   # 安装到当前用户的所有项目
```

```bash
npx skills update                    # 更新项目级 Skill
npx skills update -g                 # 更新用户级 Skill
```

`npx skills update` 会从安装时的来源仓库刷新已安装的 Skill，因此新版本不需要手动复制。加 `-y` 可跳过作用域询问，也可以用 `npx skills update codeaccord` 只更新这一个 Skill。

### 手动复制安装

将 Skill 目录复制到编码 Agent 支持的 Skill 路径。

Codex 用户级安装：

```bash
cp -R skills/codeaccord ~/.codex/skills/codeaccord
```

项目级安装：

```bash
mkdir -p /path/to/project/.agents/skills
cp -R skills/codeaccord /path/to/project/.agents/skills/codeaccord
```

其他兼容 Agent Skills 的工具，只需将 `skills/codeaccord` 复制到相应的 Skill 目录。

## 使用

显式调用：

```text
$codeaccord 支持把超过 30 秒的视频拆成多个视频卡片。
```

```text
$codeaccord 保存接口返回成功，但服务重启后配置消失了。
```

支持隐式选择 Skill 的工具，也可以根据 `SKILL.md` 中的 `description` 自动启用 CodeAccord。

### 直接实施

CodeAccord 默认在完整方案形成后停下来确认一次。用户可以明确跳过这次单独确认：

```text
$codeaccord 调查清楚后直接修复，不需要单独确认方案。
```

即使直接实施，Agent 也必须先完成只读 Explore，并在修改前给出一份标记为“已预授权”的完整 Accord；此时可以不再等待一次回复。

## 恢复 checkpoint

对话始终是主要界面。对于可能跨越上下文或会话边界的任务，CodeAccord 只维护一份简短的恢复缓存：

```text
.codeaccord/checkpoint.md
```

Agent 会在方案确认后、范围或进度发生关键变化后、长时间操作前以及预计即将压缩上下文前更新它。`Current state` 只记录恢复调查、实施或验证所必需的结论，不记录活动流水。上下文压缩或恢复会话后，Agent 先读取 checkpoint，再核对工作区。任务完成后直接删除，不归档。

checkpoint 会记录 `workspace` 和 `session`，让后续会话判断它是否属于自己。属于其他会话的 checkpoint 只会以归属提示出现，不会被当作当前任务注入，也不会在未经用户确认时被覆盖。每个工作区只有一份 checkpoint，同一工作区并发处理两个任务应改用独立 worktree。

CodeAccord 0.2 不再创建 `.codeaccord/changes/*.md`。已有文件保持不动，也不会被自动加载。

## 可选的上下文压缩 Hook

核心流程不依赖 Hook。`integrations/` 中提供 Codex 和 Claude Code 的可选示例，用于在手动压缩前检查 checkpoint，并在压缩或恢复后把 checkpoint 重新注入上下文。

Hook 不负责总结 transcript。命令 Hook 无法可靠推断 Agent 尚未保存的决策，而且 transcript 格式不是稳定契约。因此，Skill 要求 Agent 主动更新语义内容，Hook 只提供结构检查、恢复入口和归属判断。Hook 不会写入 checkpoint。

示例默认 Skill 以项目级方式安装在 `.agents/skills/codeaccord`。安装方法见[集成说明](integrations/README.md)。

## 仓库结构

```text
skills/codeaccord/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── checkpoint_hook.py

integrations/
├── README.md
├── claude-code/
│   └── settings.json.example
└── codex/
    └── hooks.json.example

tests/
└── test_checkpoint_hook.py
```

`SKILL.md` 是通用工作流；`agents/openai.yaml` 是可选的 OpenAI/Codex 界面元数据，不使用它的平台可以直接忽略。脚本和 Hook 示例也是可选能力。

## 许可证

[MIT](LICENSE)
