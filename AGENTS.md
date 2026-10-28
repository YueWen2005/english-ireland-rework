# AGENTS.md — 接管本项目的 AI 必读

> **本文件是本仓库的最高优先级文档。**
>
> 任何 AI / 自动化代理在改动本仓库之前，**必须先完整读完本文件**，并严格按本文件执行。
>
> 本文件与任何其他文档、代码注释、提交历史、口头指示冲突时，**以本文件为准**。
> 如果你认为本文件某一条是错的，**先按本文件做**，再向人类提出修改建议，不要自行绕过。

**适用对象**：所有接手本仓库的 AI 代理、协作者、以及人类维护者。
**对应版本**：v2.10.6 · **最后更新**：2026-10-28

---

## 0. 三十秒速览

| 项目 | 内容 |
|---|---|
| 这是什么 | 《钢铁雄心 IV》1.19 的**纯脚本 MOD**：爱尔兰国策树重制「翡翠岛的抉择」 |
| 技术性质 | 无 DLL、无 DLC 依赖、**不含任何自定义美术**（全部沿用原版资源） |
| 仓库结构 | 一个仓库只放一个 MOD，源码在 `mods/ire_the_emerald_isle/` |
| 规模 | 212 国策 / 160 精神 / 80 决议 / 85 事件 / 18 观点修正 |
| 改动方式 | **一律走 Pull Request**，不直接推上游 main |
| 最大风险点 | `.txt` 文件的 UTF-8 BOM（已因此出过两次事故） |

**读到这里还不够，继续往下读第 1 节。**

---

## 1. 绝对禁令

违反以下任何一条，都视为交付事故，必须回滚重做。

### 1.1 `.txt` 文件绝对不能有 UTF-8 BOM

引擎解析器遇到 BOM 会**整份拒绝**该文件，而不是报错跳过单行。后果是灾难性的：`IRE_ideas.txt` 带 BOM 时，160 个民族精神全部消失，但游戏不会崩溃，只会静默空白。

**这个坑已经踩过两次**：

| 版本 | 事故 |
|---|---|
| v2.8.1 | 本地化文件**双重 BOM** 导致国策名全乱码（v2.7.0 引入） |
| v2.9.8 | `IRE_ideas.txt` / `IRE_focus.txt` 被误加 BOM，整个精神文件被拒，民族精神全空 |

**规则**：

- `.txt`（`common/`、`history/`、`events/`）→ **无 BOM**
- `.gfx`（`interface/`）→ 与同目录已有文件保持一致（本仓库现有全部无 BOM）
- `.yml`（`localisation/`）→ **必须有 BOM**，且**只能有一个**

**每次改动后必须验证**（不要靠肉眼）：

```bash
python -c "
import glob
for f in glob.glob('**/*.txt',recursive=True)+glob.glob('**/*.gfx',recursive=True):
    if open(f,'rb').read()[:3]==b'\xef\xbb\xbf': print('带BOM:',f)
for f in glob.glob('**/*.yml',recursive=True):
    if open(f,'rb').read()[:3]!=b'\xef\xbb\xbf': print('缺BOM:',f)
"
```

### 1.2 不要自制美术资源

**2026-10-27 用户明确要求：全部沿用原版资源，不要自己画、不要自己合成。**

曾经做过一版自制顾问图标（用 Pillow 合成「相框 + 便签」卡片），虽然版式还原度不错，但用户看过后要求改回原版默认图，**接受重复脸**。

**规则**：

- 人物立绘 → 用原版 `GFX_idea_generic_*` / `GFX_portrait_*` 精灵
- 国策图标 → 用原版 `GFX_focus_*`
- 决议图标 → 用原版 `GFX_decision_*` / `generic_*`
- 旗帜 → 可以补（`gfx/flags/` 下的 TGA 属于「补全缺失」，不算自制美术），但要与同目录规格一致
- 如果确实需要新图，**先问人类**，不要自行生成

### 1.3 不要动 C 线（红线 / 黑线 IRA）

C 线由**其他人负责**，本项目的主要维护者只管 C 线以外的内容。

**属于 C 线、不要改的部分**：

- 红线（共产革命 / 世界革命）与黑线（亲德 / 新秩序）的国策
- `IRE_red_black_decisions.txt`
- 红线 / 黑线专属人物、精神、事件
- 红黑线的本地化条目

**允许碰的**：共通军事线（`IRE_M_*`）、A 线（`IRE_A_*`）、B 线（`IRE_B_*`）、共通线（`IRE_common_*`）、经济线（`IRE_E_*`）、以及 C 线也会经过的**主干节点**（例如《G2 军事情报处》）。

拿不准时，先问。

### 1.4 不要直接 push 到 upstream/main

上游有协作权限，但**仍然必须走 Pull Request**。理由是人类要看 diff。

```
origin   = https://github.com/Origin-XiChen/english-ireland-rework.git   （自己的 fork，随便推）
upstream = https://github.com/YueWen2005/english-ireland-rework.git      （协作仓库，只走 PR）
```

### 1.5 不要把设计意图当 bug 修

以下三点是**刻意的设计**，已经确认过，不要再「修复」：

| 现象 | 真相 |
|---|---|
| E 线（经济区域）与 common 线只挂在 A 线之后 | 刻意为之，目的是加强 A 线的种田能力，不是可达性缺陷 |
| AI 默认走 B 线，且 B 线内容量最少 | 刻意为之，为了减少玩家玩其他国家时 AI 爱尔兰的干扰 |
| 数值强度明显偏高 | 本意就是加强爱尔兰，**不要以平衡性为由削减产出** |

---

## 2. 协作流程

### 2.1 标准流程

```bash
# 1. 同步上游
git checkout main
git fetch upstream
git merge --ff-only upstream/main
git push origin main

# 2. 开功能分支（命名见下）
git checkout -b fix/xxx   # 或 feat/xxx、docs/xxx

# 3. 改 → 自检（见第 5 节）→ 提交
git add -A
git commit -F -            # 提交信息用 heredoc，见 2.3

# 4. 推到 fork
git push -u origin fix/xxx

# 5. 向上游提 PR
gh pr create --repo YueWen2005/english-ireland-rework \
  --base main --head Origin-XiChen:fix/xxx \
  --title "..." --body-file pr_body.md
```

### 2.2 分支命名

| 前缀 | 用途 |
|---|---|
| `feat/` | 新内容（国策、决议、事件、精神） |
| `fix/` | 修 bug |
| `docs/` | 只改文档 |
| `tweak/` | 数值 / 排版微调 |
| `chore/` | 发版、构建、杂务 |

### 2.3 提交信息风格

- 中文，第一行是概括（不加 `fix:` 之类前缀），空一行后写正文
- 正文写**为什么**，不只是**改了什么**
- 涉及具体 ID / 文件名 / 数值时写清楚
- 参考仓库历史，例如：

```
开局科技补 gw_artillery：MOD 的炮兵营模板此前无法生产火炮

《圣帕特里克营》《野鹅军团》两个师模板各带 1 个炮兵营，
但 gw_artillery 才是解锁 artillery_equipment_1 与 field_guns 的科技。
原版爱尔兰 OOB 里没有炮兵，所以原版不点这项没问题；
MOD 加了炮兵营却没给科技，等于这些精锐师的炮兵营永远补不满。
```

### 2.4 PR 正文必须包含

1. **概要**：一段话说清这个 PR 解决什么
2. **改动清单**：按模块分组，带具体 token / 数值
3. **验证结果**：跑过哪些检查（见第 5 节）
4. **是否触碰 C 线**：明确写「未触碰」或说明原因
5. **遗留问题**：本次没做的、留给后续的

### 2.5 发版流程

1. 两处版本号一起改：`descriptor.mod` 与外层 `mods/ire_the_emerald_isle.mod`
2. 跑完第 5 节自检，再进游戏实机确认一遍开局
3. **不要提交 zip**：`.gitignore` 里已经忽略 `mods/*.zip`，分发包统一走 GitHub Releases
4. 打 tag / 发 Release 由人类做，AI 只负责把源码准备好

---

## 3. 目录与文件职责

只列目录级职责与**长期稳定的关键文件**。具体有哪些文件以 `find` 为准，不要照抄本文档。

| 目录 | 职责 | 注意 |
|---|---|---|
| `common/national_focus/` | 全部国策 | **212 个国策全在 `IRE_focus.txt` 一个文件里**，改的时候小心不要破坏缩进 |
| `common/ideas/` | 国家精神 | `IRE_ideas.txt` 是主体，A 线另有 `IRE_new_world_ideas.txt` |
| `common/decisions/` | 决议与决议分类 | 分类在 `decisions/categories/`；`IRE_red_black_decisions.txt` 属 C 线 |
| `common/characters/` | 内阁、将领、领袖 | 顾问写在 `advisor = { }` 块里，见 4.5 |
| `common/scripted_effects/` | 脚本效果宏 | `IRE_effects.txt` 里放了州判定、变量阈值等共用逻辑 |
| `common/scripted_triggers/` | 脚本触发器 | |
| `common/opinion_modifiers/` | 观点修正 | |
| `common/on_actions/` | 开局 / 每日 / 每月钩子 | |
| `common/countries/` | cosmetic tag 定义 | 换国旗国名靠这个 + `set_cosmetic_tag` |
| `events/` | 剧情事件 | 两个命名空间：`ire` / `ire_nw` |
| `history/countries/` | **1936 开局设定** | 整份覆盖原版，见下 |
| `history/units/` | 师模板 + 开局编成 + 生产线 | 只写 `division_template` 不写 `units = {}` 会导致开局 0 个师 |
| `localisation/` | 中英双语 | 必须带 BOM，中英必须同步 |
| `interface/` | 精灵定义 | 新增贴图必须在这里注册 |
| `gfx/flags/` | 旗帜三档 | large 82×52 / medium 41×26 / small 10×7 |

### 3.1 两个最容易出事的文件

**`history/countries/IRE - Ireland.txt`** —— 它**整份覆盖**原版，不是增量修改。原版有的字段（`set_convoys`、`tech_trucks`、`fuel_silos`、`basic_train`、`last_election`、`election_frequency`……）只要不写就退回默认值。改这个文件时，**必须拿原版 `history/countries/IRE - Ireland.txt` 逐项对照**。

**`history/units/IRE_units.txt`** —— `division_template` 只是模板，不写 `units = { division = { ... } }` 编成块的话开局一个师都没有。

### 3.2 版本号有两处

- `mods/ire_the_emerald_isle/descriptor.mod`
- `mods/ire_the_emerald_isle.mod`（在 mod 目录**外面**）

启动器实际读的是**外层那个**。发版时两个都要改，否则启动器显示旧版本号。

## 4. 技术约定

### 4.1 缩进

- 国策树：`\tfocus = {` → `\t\tid = ...`（**1 个 tab 起，不是 2 个**）
- 决议：分类块 1 tab，决议条目 2 tab
- 一律用 **tab**，不要用空格

### 4.2 ID 前缀

| 前缀 | 含义 |
|---|---|
| `IRE_A_` | A 线：新世界爱尔兰（民主扩张） |
| `IRE_B_` | B 线：史实自由邦（中立自保） |
| `IRE_R_` | R / 红 线（共产革命）★ C 线 |
| `IRE_X_` | X / 黑 线（亲德新秩序）★ C 线 |
| `IRE_M_` | 共通军事线 |
| `IRE_E_` | 经济线（挂 A 线之后） |
| `IRE_common_` | 共通线 |
| `IRE_ira_` / `IRE_cab_` / `IRE_nw_` | IRA / 内阁 / 新世界人物 |

### 4.3 state ID（已与原版核对，不要凭印象改）

| 州 | ID |
|---|---|
| 北爱尔兰（阿尔斯特六郡） | **119** |
| 纽芬兰 | **331** |
| 伦斯特（都柏林所在州） | **113** |
| 都柏林所在**省份** | **11293** |
| 加拿大开局 23 州 | 276、464–473、682–683、739–740、860–867 |

### 4.4 本地化 key 格式

| 类型 | 格式 |
|---|---|
| 国策 | `ID` / `ID_desc` |
| 精神 | `ID` / `ID_desc` |
| 决议 | `ID` / `ID_desc` |
| 事件 | `ire.N.t` / `ire.N.d` / `ire.N.a` `b` `c`（A 线用 `ire_nw.N.*`） |
| 条件提示 | `IRE_tt_xxx`（配合 `custom_trigger_tooltip`） |
| 效果提示 | `IRE_effect_xxx`（配合 `custom_effect_tooltip`） |
| 顾问 / 人物 | `idea_token` 同时作为条目标题；`name` 可以是同一个 key，也可以是字面量 |

**中英双语必须同步**，任何新增 key 都要在两个文件里都加。当前约 2944 个 key。

### 4.5 顾问（内阁）定义机制

1.11 之后顾问写在 `common/characters/*.txt` 里，**不需要**在 `common/ideas/` 再定义一次：

```txt
IRE_cab_xxx = {
	name = IRE_cab_xxx
	gender = male
	portraits = { army = { small = GFX_idea_generic_political_advisor_europe_1 } }
	advisor = {
		slot = political_advisor          # political_advisor / army_chief / navy_chief / air_chief / high_command / theorist
		idea_token = IRE_cab_xxx
		allowed = { original_tag = IRE }
		traits = { war_industrialist }    # 必须存在于原版 00_traits.txt
		cost = 150
		ai_will_do = { factor = 1.0 }
	}
}
```

- 同一角色**可以同时**有 `corps_commander` 和 `advisor` 两个块（原版有 277 个这样的角色），用来做「将领兼理论家」
- 顾问的 `traits` 必须在 `common/country_leader/00_traits.txt` 或 `common/unit_leader/00_traits.txt` 里存在，**不要凭印象写**

### 4.6 事件命名空间

- `IRE_events.txt` → `add_namespace = ire`
- `IRE_new_world_events.txt` → `add_namespace = ire_nw`

**不要跨文件复用命名空间**，否则事件 ID 会撞。

### 4.7 条件 / 效果提示

需要给玩家看「为什么点不了 / 点了会怎样」时，用 `custom_trigger_tooltip` + `IRE_tt_*`，或 `custom_effect_tooltip` + `IRE_effect_*`，不要用裸 `has_country_flag` 直接当条件（v2.10.1 已经把 11 处裸 flag 改成了双语提示）。

---

## 5. 提交前自检清单

**每一项都要实际跑，不要凭感觉勾。**

### 5.1 文件完整性

```bash
# 在 mod 源码目录下执行
cd mods/ire_the_emerald_isle

python -c "
import glob
bad=[]
for f in glob.glob('**/*.txt',recursive=True)+glob.glob('**/*.gfx',recursive=True):
    raw=open(f,'rb').read()
    if raw[:3]==b'\xef\xbb\xbf': bad.append(('BOM',f))
    if raw.count(b'{')!=raw.count(b'}'): bad.append(('括号',f))
for f in glob.glob('**/*.yml',recursive=True):
    if open(f,'rb').read()[:3]!=b'\xef\xbb\xbf': bad.append(('缺BOM',f))
print(bad or 'OK')
"
```

### 5.2 引用闭合

- 新增的 `idea_token` → 本地化有对应 key，且不与 `common/ideas/` 已有 token 冲突
- 新增的 `GFX_*` 精灵 → 在 `interface/*.gfx` 或原版 gfx 里有定义
- 新增的 `recruit_character` → 目标角色 ID 存在
- 新增的 `traits` → 在原版特质文件里存在
- 新增国策 → `prerequisite` / `mutually_exclusive` 指向的 ID 都存在

### 5.3 同步到游戏目录

```bash
# 源码 → 已安装副本，改完必须同步，否则进游戏看不到改动
cp -a mods/ire_the_emerald_isle/. \
  "C:/Users/<用户名>/Documents/Paradox Interactive/Hearts of Iron IV/mod/ire_the_emerald_isle/"
diff -rq mods/ire_the_emerald_isle \
  "C:/Users/<用户名>/Documents/Paradox Interactive/Hearts of Iron IV/mod/ire_the_emerald_isle"
```

### 5.4 不要相信旧的 error.log

`Documents/Paradox Interactive/Hearts of Iron IV/logs/error.log` 会跨版本累积。**先看 `game.log` 里的 Start-date**：如果那是某个旧存档的读档，日志里的 `Invalid idea`、作用域报错绝大多数是**版本漂移存档**的产物，与当前代码无关。

判断方法：把日志里报错的 token 拿去当前源码里 grep，如果全都在，就说明是旧存档的问题，不要去改代码。

---

## 6. 已知的坑

| 症状 | 根因 | 处置 |
|---|---|---|
| 民族精神全空 / 国策树整块消失 | `.txt` 带 BOM | 去 BOM，见 1.1 |
| 国策名乱码 | `.yml` 双重 BOM | 只保留一个 BOM |
| `Invalid idea: X` 但源码里明明有 | 读的是旧版本存档 | 看 `game.log` 的 Start-date，不要改代码 |
| 开局 0 个师 | `history/units/*.txt` 只有 `division_template` 没有 `units = {}` | 补 `units = {}` 编成块 |
| 开局 0 艘运输船 | 覆盖 `history/countries/` 时漏了 `set_convoys` | 补回，且注意爱尔兰**没有船坞**，这是唯一来源 |
| 精锐师炮兵营永远空装 | 缺 `gw_artillery` 科技 | 补科技；`gw_artillery` 才是解锁 `artillery_equipment_1` + `field_guns` 的 |
| 小旗位显示空白 | `gfx/flags/small/` 缺对应 TGA | 按 10×7 / 32bpp 补齐 |
| 顾问头像空白 | 精灵名写错（例：`GFX_idea_generic_head_of_intelligence_western_european_2` 实际是 `..._2d`） | 去原版 `interface/*.gfx` 里 grep 全名 |
| 启动器显示旧版本号 | 只改了 `descriptor.mod`，没改外层 `mods/ire_the_emerald_isle.mod` | 两个都改 |

**正则小坑**：用脚本扫 `traits = {` 时，`portraits` 里也含 "traits" 三个字母，会被误匹配。用 `(?<!por)\btraits` 或直接匹配 `\n\t\ttraits\s*=`。

---

## 7. 速查

### 7.1 常用命令

```bash
# 同步上游
git fetch upstream && git merge --ff-only upstream/main

# 看上游有没有新东西
git log --oneline main..upstream/main

# 统计规模
grep -c "focus = {" mods/ire_the_emerald_isle/common/national_focus/IRE_focus.txt

# 找国策 ID
grep -n "id = IRE_A_" mods/ire_the_emerald_isle/common/national_focus/IRE_focus.txt
```

### 7.2 当前规模（v2.10.6）

| 项目 | 数量 |
|---|---|
| 国策 | 212 |
| 精神 | 160 |
| 决议 | 80（18 个分类） |
| 事件 | 85 |
| 观点修正 | 18 |
| 本地化键 | ~2946 |
| 人物（MOD 新增） | 15（10 名内阁与顾问 + 5 名新世界人物，v2.10.6 起） |

### 7.3 游戏本体与工具

游戏装在 Steam 库里，**可能不在默认路径**。当前开发机的实际路径如下，换机器时先确认自己的路径，不要照抄：

```
C:\software\Steam\steamapps\common\Hearts of Iron IV
```

需要脚本时优先用 Python（本机有 Pillow，可读写 TGA / DDS）。纯文本操作用 grep / sed 就够，不要引入依赖。

---

## 8. 交接说明

### 8.1 接手时按这个顺序读

1. **本文件**（你正在读）
2. `README.md` —— 项目概览与版本进度
3. `mods/ire_the_emerald_isle/README_爱尔兰MOD.md` —— 机制细节与引擎限制
4. `mods/ire_the_emerald_isle/差异对照表.md` —— 设计文档 → 实际实现的逐条对照
5. `common/national_focus/IRE_focus.txt` —— 真正的「事实来源」，一切以代码为准

### 8.2 开工前先确认

- [ ] 读完本文件
- [ ] `git status` 干净，`main` 已同步 upstream
- [ ] 知道这次改动属于哪条线，是否触碰 C 线
- [ ] 知道改完要跑第 5 节的自检

### 8.3 改本文件的规则

本文件是**规则**，不是**日志**。修改它需要：

1. 说明为什么现有规则不够用
2. 同步更新顶部的「最后更新」日期
3. 走 PR，让人看过再合

版本进度的流水账写在 `README.md`，**不要写进本文件**。

---

*本文件优先级高于仓库内一切其他文档。冲突时以本文件为准。*
