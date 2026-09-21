# CodeAccord

**先就变更达成一致，再完成实现。**

CodeAccord 是一个轻量、可移植的软件变更 Agent Skill，统一处理产品需求、Bug 修复、重构、配置调整和其他代码库工作：

```text
调查 -> 质疑 -> 确认 -> 实施 -> 验证
```

Agent 会先调查真实项目，检验用户和自己的假设，形成一份具体的变更方案，取得一次明确确认，再完成实施和验证。

[English](README.md)

## 为什么需要 CodeAccord

编码 Agent 容易走向两个极端：问题尚未查清就开始修改，或者给日常工作套上过重的规划流程。CodeAccord 保留规格驱动开发中真正有用的边界，同时控制流程成本：

- 只有一个 Skill；
- 只有一个方案确认点；
- 不需要 CLI 或运行时依赖；
- 不强制创建规划文件；
- 复杂变更最多维护一份持久变更记录；
- 不自动执行规格同步或归档。

用户决定想得到的产品结果，Agent 仍必须根据源码、测试、日志、契约和项目约束判断用户提出的原因和实现方案是否成立。

## 工作流

| 阶段 | 作用 |
| --- | --- |
| 调查 | 从真实项目中确认当前行为、调用链和证据。 |
| 质疑 | 检验假设、发现风险，并提出有依据的推荐方案。 |
| 确认 | 给出一份可审查的完整范围，取得一次明确确认。 |
| 实施 | 完成已确认的代码、测试和必要文档。 |
| 验证 | 对照验收标准检查结果并报告证据。 |

CodeAccord 在同一套工作流中识别产品需求、Bug 和混合变更。用户不需要反复强调“先分析”或“暂时不要改代码”。

## 安装

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

即使直接实施，Agent 也必须先完成必要调查。

## 持久变更记录

简单任务只保留在对话中。跨模块或跨会话、影响接口/数据/部署/运维、包含多个产品决策，或者用户要求保存方案时，CodeAccord 才创建一份变更记录。

项目没有规定其他兼容目录时，默认位置为：

```text
.codeaccord/changes/<change-name>.md
```

CodeAccord 不会自动修改忽略规则，也不会自动提交、同步或归档变更记录。

## 仓库结构

```text
skills/codeaccord/
├── SKILL.md
└── agents/
    └── openai.yaml
```

`SKILL.md` 是通用工作流；`agents/openai.yaml` 是可选的 OpenAI/Codex 界面元数据，不使用它的平台可以直接忽略。

## 许可证

[MIT](LICENSE)
