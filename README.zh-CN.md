# CodeAccord

**先明确可验证的目标；明确任务直接完成。**

CodeAccord 是一个轻量、以对话为主的规格驱动开发（SDD）Agent Skill，适用于新需求、Bug 修复、重构和配置调整：

```text
探索 [调查 <-> 质疑] -> [必要时确认方案] -> 实施 -> 验证
```

Agent 会先检查真实项目并检验假设，以用户请求或已确认的方案明确预期行为和验证方式。目标明确且没有需要用户决定的问题时，直接实施和验证；需要讨论行为或边界时，先比较有实际差异的方案，再用简明的结论供用户确认。

[English](README.md)

## 为什么需要 CodeAccord

编码 Agent 容易在问题未查清时动手，也容易为明确任务套上过重的规划流程。CodeAccord 保留必要的判断，同时减少无用的方案输出：

- 明确任务以用户请求作为最小规格，直接处理，不额外输出方案或等待确认；
- 有实质性决策时才讨论并确认一次；
- 需要确认的方案先用一句话说清结论，再展开必要依据；
- 对话是主要工作界面；确认的方案或需要跨上下文恢复的任务使用一份临时 checkpoint；
- 核心流程不需要 CLI 或运行时依赖，也不累积 change 文件。

用户决定期望的结果，Agent 仍应根据源码、测试、日志和契约判断原因与实现方式是否成立。

## 工作流

| 阶段 | 作用 |
| --- | --- |
| 探索 | 调查真实行为并检验假设；明确任务可简短完成这一阶段。 |
| 确认方案（按需） | 仅在需要用户决定重要行为或边界时，整理清晰的推荐方案并取得一次确认。 |
| 实施 | 完成已授权的代码、测试和必要文档。 |
| 验证 | 对照用户请求或已确认方案检查结果并报告证据。 |

## 按需确认的方案

只有存在实质性的产品、兼容性、数据、部署等决策，或用户明确要求先讨论时，才进入方案讨论。方案的**第一句话应完整说明原因或目标、推荐做法、主要修改位置和预期结果**，让人不翻前文也能看懂。后面只展开判断所需的证据、影响范围、风险和验收，不堆调查流水。

Bug 可以按“原因与证据 → 修复办法 → 修改位置 → 验证”组织；新需求可以按“真实的方案取舍 → 推荐实现 → 影响范围 → 验收”组织。标题、顺序和篇幅依任务调整，并使用用户的语言。不要为填模板虚构备选方案，也不要把未证实的根因写成事实。

仍有用户决策未解决时继续讨论，不请求确认不完整的方案。方向已经明确且用户已授权实施时，直接继续；否则只确认一次。后续若出现超出授权范围的重要变化，只说明变化及影响，不重复整份方案。

## 明确任务直接实施

用户要求修改或修复，目标与预期结果明确且没有待定的实质性决策时，Agent 先从用户请求和项目契约中确定可观察的预期行为及验证方式；Bug 还需区分当前行为与预期行为。若关键预期无法推导，才就缺失的决策澄清。调查到足以安全实施后，直接修改并按该预期验证。无需额外输出方案、另写规格文件或再次确认；涉及多个文件也不自动触发方案。Bug 的根因可在调查中确定，不必在开始调查前就已知。

需要用户决定行为或兼容性边界时，先只读调查并讨论。普通工程实现选择由 Agent 负责；提交、推送、部署、发布、删除持久数据等操作仍按各自授权处理。

## 安装

### 将提示词发送给你的 AI 安装

将下面这句话复制发送给你的编码 Agent，Agent 会自动完成安装：

> 请根据 https://github.com/6xdax/CodeAccord，安装 CodeAccord skill，安装到当前项目的 `.agents/skills/` 目录。

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

明确任务默认可以直接处理，例如：

```text
$codeaccord 调查并修复保存接口重启后丢失配置的问题。
```

用户也可以明确要求先讨论方案；此时 Agent 保持只读调查，直到方向和授权范围确定。

## 恢复 checkpoint

对话始终是主要界面。对于可能跨越上下文或会话边界的任务，CodeAccord 只维护一份简短的恢复缓存：

```text
.codeaccord/checkpoint.md
```

直接任务是否创建 checkpoint 取决于恢复风险，无需额外确认；任务可能跨越上下文或长时间操作时，记录用户已授权的范围。需要确认方案的任务则在确认后、修改产品文件前写入并核验 checkpoint。之后在关键进度、长时间操作前和预计压缩上下文前更新它。`Current state` 只记录恢复调查、实施或验证所必需的结论，不记录活动流水。上下文压缩或恢复会话后，Agent 先读取 checkpoint，再与 Git HEAD、状态和当前源码对账，刷新过期状态后才能继续修改。任务完成后直接删除，不归档。

checkpoint 会记录 `workspace`、`session`、回复语言、Accord revision、Git HEAD、工作区指纹和最近一次刷新原因。工作区指纹覆盖暂存修改、未暂存的已跟踪修改和未跟踪内容，但不会保存实际 diff。记录为其他会话的 checkpoint 视为外来状态：Agent 会先与用户确认，再决定是否继续该任务或覆盖它。每个工作区只有一份 checkpoint，同一工作区并发处理两个任务应改用独立 worktree。

CodeAccord 0.2 不再创建 `.codeaccord/changes/*.md`。已有文件保持不动，也不会被自动加载。

## 仓库结构

```text
skills/codeaccord/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── scripts/
    └── checkpoint_snapshot.py

tests/
└── test_checkpoint_snapshot.py
```

`SKILL.md` 是通用工作流；`agents/openai.yaml` 是可选的 OpenAI/Codex 界面元数据，不使用它的平台可以直接忽略。快照脚本也是可选能力。

## 许可证

[MIT](LICENSE)
