# 英语爱尔兰重置 · English Ireland Rework

> 《钢铁雄心 IV》爱尔兰国策树重制 MOD 仓库。

# English Ireland Rework

> A Hearts of Iron IV mod repository — reworking Ireland's national focus tree.

## MOD 列表

| MOD | 版本 | 说明 |
|---|---|---|
| [翡翠岛的抉择 - 爱尔兰国策树](mods/ire_the_emerald_isle/) | 2.0.0 | 爱尔兰双主线国策树，57 国策 / 17 决议 / 40 精神 / 7 事件 |

---

## 安装方法

### 方式一：用压缩包（推荐）

1. 下载 [`mods/翡翠岛的抉择_爱尔兰MOD.zip`](mods/翡翠岛的抉择_爱尔兰MOD.zip)
2. 解压到：
   ```
   C:\Users\<用户名>\Documents\Paradox Interactive\Hearts of Iron IV\mod\
   ```
3. 打开游戏启动器 → 播放集 → 勾选「翡翠岛的抉择 - 爱尔兰国策树」

解压后的目录应该是：

```
mod\
├── ire_the_emerald_isle.mod
├── ire_the_emerald_isle\
└── 差异对照表.md
```

> 如果解压工具自动建了一层同名文件夹，需要把里面的内容手动移到 `mod\` 根目录下，否则启动器扫描不到。

### 方式二：手动装（想改脚本时）

把 `mods/ire_the_emerald_isle.mod` 和整个 `mods/ire_the_emerald_isle/` 文件夹复制到上面的 `mod\` 目录。

---

## 环境要求

- **钢铁雄心 IV 1.17.\***
- 不需要任何前置 MOD（无 DLC 依赖）
- 整个 MOD 只用原版美术资源，不含自定义图片/模型/音乐，体积约 100 KB

---

## 目录说明

```
mods/
├── ire_the_emerald_isle/           MOD 源码
│   ├── common/
│   │   ├── national_focus/         57 个国策
│   │   ├── ideas/                  40 个国家精神
│   │   ├── decisions/              17 个决议
│   │   ├── opinion_modifiers/      16 个观点修正
│   │   ├── scripted_effects/       脚本效果宏
│   │   └── on_actions/             开局/每日/每月钩子
│   ├── events/                     7 个剧情事件
│   ├── history/                    开局设定 + 师模板
│   ├── localisation/               简体中文本地化
│   └── README_爱尔兰MOD.md         详细的机制说明与已知限制
├── ire_the_emerald_isle.mod        启动器识别文件
├── 差异对照表.md                    设计文档 → 实际实现 的逐条对照
└── 翡翠岛的抉择_爱尔兰MOD.zip       打包版（内容同上）
```

---

## 已知限制

**动态国名未实现**。Éire / 凯尔特联邦 / 爱尔兰共和国 / 爱尔兰-纽芬兰联邦这四个国名变化没有做，原因是需要覆盖整份 `common/country_tags/`（约 1.5 MB），与其他 MOD 一定冲突。阶段感通过国家精神体现。

**state ID 需要按你的游戏版本核对**。脚本假设北爱尔兰是 113–118、纽芬兰是 331。如果你的游戏或地图 MOD 有偏移，进游戏后控制台输入 `tdebug`，鼠标悬停省份看左上角的 State ID，然后改：

- `common/scripted_effects/IRE_effects.txt`
- `common/decisions/IRE_decisions.txt`
- `common/national_focus/IRE_focus.txt`

其余引擎限制（特殊建筑、渔农产品资源、精英师模板修正等）见 `mods/ire_the_emerald_isle/README_爱尔兰MOD.md`。
