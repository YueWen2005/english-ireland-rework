# 翡翠岛的抉择 - 爱尔兰国策树 MOD

为钢铁雄心 4（1.17.*）实现的完整爱尔兰双主线国策树。

## 安装

把 `ire_the_emerald_isle.mod` 和 `ire_the_emerald_isle/` 文件夹复制到：

```
C:\Users\<用户名>\Documents\Paradox Interactive\Hearts of Iron IV\mod\
```

启动器 → 播放集 → 勾选「翡翠岛的抉择 - 爱尔兰国策树」。

---

## 内容

- **双主线起点（互斥）**：《边境公投》（架空，开局拿北爱）/《自由邦的巩固》（史实）
- **A 线**：北爱整合 → 跨海网络 → 纽芬兰/美国/墨西哥/南美四支线 → 凯尔特联邦；另有独立紧急状态分支与外交线（多尼戈尔走廊、港口换统一）
- **B 线**：内政巩固 → 英爱贸易 → 1937 宪法 → 紧急状态 → 中立三选一 → 1949 共和国 → 最后的统一
- **经济区域**：香农水电、泥炭、科克港、福因斯飞艇港、中央银行、医院彩票、战后香农自由区
- **军事区域**：需二战爆发 + 紧急状态完成后解锁；陆军 / 海军 / 空军 / 情报 / 海岸瞭望 / 装甲车
- **93 个国策节点**
- **13 个剧情事件**、**17 个决议**
- **72 个国家精神**
- 完整简体中文本地化

### 三个核心变量机制

| 变量 | 范围 | 用途 |
|---|---|---|
| `IRE_plebiscite_support` | 0–100（初值 45） | 决定拿回北爱的质量（三档：惊险 / 顺利 / 压倒性） |
| `IRE_diaspora_network` | 0–100 | 跨海路线的进度条（20/40/60/80/100 解锁五档精神） |
| `IRE_neutral_credibility` | 0–100（初值 50） | 影响走私收入档位（40/60/80PP）与调停者成功率（30%/45%/60%） |
| `IRE_nf_support` | 0–100 | 纽芬兰亲爱派支持度（≥50 可发起自治领公投） |

---

## 引擎限制（5 处无法逐字实现，均给出替代）

| # | 文档要求 | HOI4 限制 | 本 MOD 的处理 |
|---|---|---|---|
| 1 | 四国动态国名（Éire / 凯尔特联邦 / 爱尔兰共和国 / 爱尔兰-纽芬兰联邦） | 需覆盖整份 `common/country_tags/`（约 1.5MB），与其它 MOD 必冲突 | **未实现**。阶段感由精神与国策描述体现 |
| 2 | 哈兰德与沃尔夫「特殊建筑」 | 建筑类型固定，不能自定义 | 用精神 `IRE_haaland_wolff` 表达：船坞建造速度 +10%、船坞产出 +10% |
| 3 | 「鱼类 +8」「牛肉 +8 / 小麦 +6」 | 只有 6 种资源（油/铝/橡胶/钨/钢/铬） | 转精神：`IRE_newfoundland_fisheries`（消费品 −3%、出口 +5%）、`IRE_south_american_trade`（出口 +8%、消费品 −3%） |
| 4 | 精英师「模板修正」绑定到某个模板 | 无 per-division modifier | `history/units/` 预声明模板 + `create_unit` 实例化 + 国家级精神 `IRE_san_patricio_elite`（攻+15/防+10/组织+15）。**负面项不实现**（会波及全军） |
| 5 | 「移除农业穷国的一半负面」 | 精神只能整条增删 | 替换为 `IRE_agrarian_poverty_lite`（只留消费品 +5%） |

**另一处宽松处理**：《跨大西洋补给网》文档要求「完成 ≥2 条美洲支线」，脚本实现为「三条支线任一」（更宽松）。如需严格按 ≥2 条，把 `IRE_A_supply_web` 的 `OR` 改为统计变量即可。

---

## 需要注意 / 待核对

### 1. 北爱尔兰六郡 state ID

脚本假设 **113–118**。核对方法：开档后控制台输入 `tdebug`，鼠标悬停北爱各省份，左上角显示 `State ID`。
如需修改，改这两处：
- `common/scripted_effects/IRE_effects.txt` → `IRE_core_northern_ireland`
- `common/decisions/IRE_decisions.txt` → `IRE_dublin_order`

### 2. 纽芬兰 state ID

脚本假设 **331**。同样用 `tdebug` 核对。
如需修改，改这两处：
- `common/scripted_effects/IRE_effects.txt` → `IRE_annex_newfoundland`
- `common/national_focus/IRE_focus.txt` → `IRE_A_nf_province`（建厂落点）

### 3. 开局历史文件

`history/countries/IRE - 爱尔兰.txt` **整份替换**了原版爱尔兰的开局设定（原版文件也叫这个名）。
本文件只保留最小可玩配置：科技、3 个研究槽、政体与四开局 debuff、以及自定义 `oob`。
如果你同时装了其它改爱尔兰的 MOD，会有冲突——把这份文件删掉即可（国策树本身仍能用，只是没有自定义师模板）。

### 4. 自定义师模板

`history/units/IRE_units.txt` 定义了三个模板：
- `San Patricio Battalion`（9步+1炮+工兵/侦察/野战医院）
- `LDF Militia`（3步+工兵）
- `IRE_Infantry Division`（6步+工兵）

由 `history/countries/IRE - 爱尔兰.txt` 的 `oob = "IRE_units"` 加载。

### 5. 公投时序

《边境公投》完成后 **不立即** 触发北爱公投事件。玩家有约 140 天的窗口去：
- 刷《统一宣传运动》决议（+12/次，最多 5 次）
- 把稳定度顶到 60% 拿 +10
- 走《大流散的遗产》拿 +20（未公投时）

公投由 `IRE_A_belfast`（贝尔法斯特整合）触发。这样 45 → 最高 100 的支持度分档才有意义。

---

## 本版修复的 Bug（14 项）

| # | 问题 | 状态 |
|---|---|---|
| B1 | 三条中立国策用 3 个并列 `prerequisite` = AND，配合 `IRE_B_plan_w` 的关系门槛导致**整条 B 线死锁** | 已改为 `OR { coastal / ldf / plan_w }` |
| B2 | `IRE_A_irish_division` 里的 `load_focus = IRE_A_boston` 会跳回已完成国策 | 已删除 |
| B3 | 三条中立国策 `y = 8` 与 coastal/plan_w 挤在同一层 | 已移到 y=10，下游全部 +1 顺延 |
| B4 | 《大流散的遗产》固定给稳定度，「+20 支持度」永远拿不到 | 已改为 `if / else` 双分支 |
| N1 | **6 处 `2 = { ... }` 硬编码——州 ID 2 不是爱尔兰的州**，工厂/海军基地建到别国 | 全部改为 `random_owned_controlled_state` |
| N2 | 三条中立国策 `mutually_exclusive` 缺 `focus =` 前缀 → 互斥失效 | 已补 |
| N3 | 宣传决议里的 `modifier = { ... = yes }` 是非法语法 | 已删除（`complete_effect` 里已有 +12） |
| N4 | `random_events = { 250 = 0 }` 指向不存在的事件 0 | 改为 `on_daily` 判断 3.17 + 年度 flag |
| N5 | `has_ideas =` 应为单数 `has_idea` | 已修正 |
| N6 | 本地化文件无 UTF-8 BOM | 已补 |
| N7 | **20 处 `add_opinion` 传数字**，但 `modifier` 参数要 `opinion_modifiers` token | 新建 `common/opinion_modifiers/IRE_opinions.txt`，全部替换 |
| N8 | `IRE_annex_newfoundland` 要求纽芬兰是 ENG **核心**，否则静默失败 | 改为直接作用域 `331 = { transfer_state = ROOT }` |
| N9 | `IRE_core_northern_ireland` 依赖 `state = x` 触发器 | 改为直接作用域 `113 = { add_core_of = ROOT }` |
| N10 | 中立三条国策的 `prerequisite` 语法错误连带 `IRE_B_emergency` 下游全部错位 | 坐标已重排 |

---

## 校验记录

全部通过：
- 57 节点无重复 ID、**坐标零重叠**（脚本按 `relative_position_id` 链重算绝对坐标）
- 全部国策有标题与描述本地化
- 全部 40 个精神定义 ↔ 引用闭合
- 全部 17 条决议有本地化
- 全部 16 个脚本效果定义 ↔ 调用闭合
- 全部 7 个事件定义 ↔ 引用闭合
- 全部 16 个观点修正 token 定义 ↔ 引用闭合
- 所有 `.txt` 括号平衡
- 本地化 UTF-8 BOM 已确认

---

## 文件结构

```
ire_the_emerald_isle/
├── common/
│   ├── national_focus/IRE_focus.txt          57 国策
│   ├── ideas/IRE_ideas.txt                   40 精神
│   ├── decisions/IRE_decisions.txt           17 决议
│   ├── opinion_modifiers/IRE_opinions.txt    16 观点修正
│   ├── scripted_effects/
│   │   ├── IRE_effects.txt                   效果宏（网络/信誉/核心化/紧急状态分级）
│   │   └── IRE_init.txt                      变量初始化
│   └── on_actions/IRE_on_actions.txt         开局/每日/每月钩子
├── events/IRE_events.txt                     7 事件
├── history/
│   ├── countries/IRE - 爱尔兰.txt            开局设定 + oob 引用
│   └── units/IRE_units.txt                   3 个师模板
├── localisation/english/IRE_l_english.yml    中文文本
└── descriptor.mod
```
