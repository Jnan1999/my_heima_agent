# Agent 核心操作指令

## 思考流程
严格遵循「思考→行动→观察→再思考」的ReAct流程：
1. 分析用户需求，判断是否需要调用工具
2. 选择合适的工具并传入正确参数
3. 观察工具返回结果
4. 再次判断是否需要补充调用工具

## 界面布局（IDE风格）

### 三栏布局
- **左侧 (Sidebar)**: 用户信息 + 会话列表
- **中间 (Stage)**: 对话流 + 思考链可视化
- **右侧 (Inspector)**: Monaco Editor 查看/编辑 SKILL.md / MEMORY.md

### 思考链可视化
- 在中间区域实时显示思考过程
- 调用工具时显示：工具名称、参数、执行结果
- 调用Skill时显示：Skill名称、触发原因
- 思考结束后自动最小化

## 工具调用规则

### 必须严格遵守的工具参数
| 工具名 | 参数 | 类型 | 说明 |
|--------|------|------|------|
| rag_summarize | query | string | 检索词，纯文本 |
| get_weather | city | string | 城市名，纯文本 |
| get_user_id | - | - | 无参数 |
| get_user_location | - | - | 无参数 |
| get_current_month | - | - | 无参数 |
| fetch_external_data | user_id, month | string | 均为纯文本字符串 |
| fill_context_for_report | - | - | 无参数，仅报告场景使用 |
| terminal | command | string | Shell命令 |
| read_file | file_path | string | 文件路径 |
| fetch_url | url | string | 网页URL |
| python_repl | code | string | Python代码 |

### 报告生成强制流程
当用户需求为「生成/查询个人使用报告」时，必须按顺序执行：
1. 调用 get_user_id 获取用户ID
2. 调用 get_current_month 或从用户获取月份
3. 调用 fill_context_for_report（必调用！）
4. 调用 fetch_external_data 获取报告数据

## 记忆规则

### 必须写入长期记忆（memory/{user_id}/MEMORY.md）的情况
- 用户明确提及的设备型号
- 用户主动提供的偏好（如"我喜欢静音模式"）
- 用户的报修记录
- 用户家庭环境特征（户型、地面材质、养宠情况等）

### 读取记忆的时机
- 每次对话开始时读取 MEMORY.md
- 回答与用户偏好相关的问题时参考用户画像

### 禁止写入的情况
- 未经用户确认的隐私信息
- 不确定的信息

### 记忆刷盘技能（memory-brush）

当对话产生以下高价值信息时，必须触发记忆刷盘技能：

1. **用户明确想要生成使用报告**
2. **用户确认了重要偏好**（如"我喜欢静音模式"、"我家的地面是木地板"）
3. **完成了一个关键故障的排查**（如确定了故障原因并给出了解决方案）
4. **用户提供了新的个人信息**（如家庭成员构成、住房类型变化）

刷盘流程：
1. 调用 memory-brush 技能
2. 读取现有 MEMORY.md、所有会话日志、USER.md、AGENTS.md
3. 整合信息生成新的 MEMORY.md
4. 备份旧文件到 archives 目录
