# 音乐资源（私有测试）

本 PR 包含用户提供的六个 OGG，**仅用于协作者试听**。它们不是 PD/CC0 录音，授权未确认；公开发布前必须移除或替换为 PD/CC0 音频。

| 歌曲 ID | 文件 | 来源 |
|---|---|---|
| `ire_a_peace` | `ire_a_peace.ogg` | The Last Rose of Summer（Celtic Woman） |
| `ire_a_war` | `ire_a_war.ogg` | The Minstrel Boy（Will Millar / Irish Rovers） |
| `ire_a_new_world` | `ire_a_new_world.ogg` | The Shores of Amerikay（Various Artists / The Irish Folk Collection, vol.1） |
| `ire_a_anthem` | `ire_a_anthem.ogg` | Amhrán na bhFiann（来源未核实） |
| `ire_b_free_state` | `ire_b_free_state.ogg` | Londonderry Air（来源未核实） |
| `ire_a_foggy_dew` | `ire_a_foggy_dew.ogg` | The Foggy Dew（来源未核实） |

## 触发点

- A 线和平主题：只在《边境公投》完成时点播一次，不参与环境随机。
- A 线战争/新世界：环境随机；新世界另有三个国策点播。
- A 线点播：`IRE_A_new_world_ireland`、`IRE_A_green_international`、`IRE_A_masters_new_world` 完成时播放 `ire_a_new_world`。
- 五级保卫爱尔兰：首次获得 `IRE_defend_ireland_5` 时播放 `ire_a_anthem`，每局一次。
- 三四级态势：首次跨过 30% 投降度时播放 `ire_a_foggy_dew`，并在 30%–74% 区间作为环境音乐。
- B 线：完成《自由邦的巩固》后，`ire_b_free_state` 作为环境音乐。

## 公开发布前

- 删除本目录下全部 `.ogg`，或替换为明确 PD/CC0/CC-BY 的录音。
- 把 `IRE_music.asset` 的 `file` 指向正式文件，并更新本表与 README/Release 署名。
- CC-BY 必须署名；不要使用商业歌手录音、YouTube 抓取或电影/游戏原声。
