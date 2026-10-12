# 差异化分析：mcd-a11y-counter 与 RANKING.md 128 个已上榜项目

数据源：`M-China/mcd-developer-innovation-challenge` → `RANKING.md`
更新时间 2026-10-12 16:00:35，共 128 条（含并列排名）。

分析方式：按项目名称与定位语义聚类，统计各赛道占用数，定位 `mcd-a11y-counter` 的位置。

---

## 一、榜单全景：哪些地方不要去

| 赛道 | 项目数 | 代表项目（Star） | 拥挤度 |
|---|---:|---|---|
| 优惠券 / 省钱 / 最优凑单 | 25+ | mcd-coupon-strategist(175)、mcd-budget-meal(93)、mcd-saver-strategist(36)、mcd-cart-optimizer(19) | 🔴 |
| 卡路里 / 减脂 / 宏观营养 | 20+ | mcd-order-calories(37)、mcd-calorie-budget-skill(23)、mcd-nutrition-optimizer(6)、mcmuscle-ai(4) | 🔴 |
| 通用点餐助手 / 管家 | 20+ | McLife-Desk(49)、mcd-meal-brain(14)、mcd-meal-butler(11)、mcd-butler(6) | 🔴 |
| 人格 / 情绪 / 玄学 | 12+ | mcd-mbti(36)、mcd-persona-card(10)、mcd-mood-palette(6)、mcd-fortune(30) | 🟠 |
| 派对 / 生日 / 聚会 | 8+ | mcd-party-officer(85)、mcd-party-buddy(18)、mcd-party-planner(5)×2 | 🟠 |
| 记忆 / 年度总结 / 档案 | 7 | mcd-memory-can(11)、mcd-wrapped(11)、mcd-order-memory(8) | 🟡 |
| 积分 / 会员权益 | 6 | mcperks-planner(29)、mcd-points-vault(17)、mcd-points-actuary(16) | 🟡 |
| 极客向（CLI / git / 终端） | 5 | mcd-git(44)、mcd-terminal(18)、mcd-1024-skill(21) | 🟡 |
| 活动情报 / 周边追踪 | 5 | mcd-event-radar(70)、mcd-merch-intel(15)、mcd-grail-radar(14) | 🟡 |
| 拼单 / 请客 / 代付 | 4 | mcd-send-a-meal(5)、mcd-group-order-mate(5)、mcd-group-order-captain(4) | 🟡 |
| 提醒 / 到期管理 | 3 | mcd-expiry-butler(6)、mcd-pin-reminder(6) | 🟢 |
| 游戏化 / Roguelike | 3 | mcd-rogue(5)、mcd-roguelike-order(4) | 🟢 |
| 早餐专项 | 2 | mcd-breakfast-variety(25)、mcd-low-cal-breakfast(5) | 🟢 |
| 咖啡 / 茶饮专项 | 2 | mcd-cafe-decoder(4)、mcd-tea-captain(4) | 🟢 |
| 门店地理可视化 | 1 | mcd-china-map(25) | 🟢 |
| 得来速 | 1 | mcd-mcdrive-mate(17) | 🟢 |
| 语音点餐 | 1 | mcd-voice-order-assistant(15) | 🟢 |
| 忌口定制（去酸黄瓜） | 1 | mcd-no-pickle(17) | 🟢 |
| 儿童乐园餐 | 1 | MCD-happy-meal(34) | 🟢 |
| **适老 / 无障碍 / 老年友好** | **0** | —— | **⚪ 空** |

---

## 二、唯一的近似项，以及为什么它不算

榜单里最接近的是 **`mcd-voice-order-assistant`（15 Star）**。

| 维度 | mcd-voice-order-assistant | mcd-a11y-counter |
|---|---|---|
| 解决什么 | **输入方式**：用嘴代替手 | **认知负荷**：决策数量本身太多 |
| 目标用户 | 想偷懒的普通用户 | 老年人 / 视障 / 低数字素养 / 代下单的子女 |
| 菜单呈现 | 不变，仍是 15 个分类、110 个 SKU | 收敛到 ≤3 个选项 |
| 输出可读性 | 未处理 | 12 条无障碍规约（无表格、元/角读法、口语时刻） |
| 代际场景 | 无 | 子女远程决策 + 给爸妈的取餐卡 |
| 默认偏好 | 无 | 少冰、去酱、换无糖、低钠 |
| 健康护栏 | 无 | 高血压钠过滤、控糖换无糖（0 差价） |

两者不冲突：语音解决"怎么说"，无障碍解决"要决定多少次"。一个咽部有疾病的老人可以说得很清楚，但仍然面对一屏看不懂的菜单。

其余涉及「适化 customize」的只有 `mcd-no-pickle`（去酸黄瓜），是**单个忌口梗**，不是无障碍设计。

---

## 三、三步各自的差异化来源

### 第 1 步 · 定地方 —— 用 `distance` + 营业时段做减法

| 已有项目怎么用门店数据 | 本 skill 怎么用 |
|---|---|
| `mcd-china-map`(25)：地图可视化，展示多家门店分布 | 只展示 **1 家**，其余全部不告诉用户 |
| `mcd-now`(9)、`mcd-chill`(22)：按"此刻"给情绪化推荐 | 用 `businessStartTime/EndTime` 做**硬校验**，含跨夜门店（18:00–06:00） |
| —— | `distance` → 老年步速 50 米/分钟的**走路分钟**（成年人的经验值是 80） |
| —— | 打烊倒计时：剩余 ≤30 分钟主动劝退，>60 分钟才正常呈现 |
| —— | >800 米直接建议改送外送 |

### 第 2 步 · 定吃的 —— 复用历史 + 四道过滤

| 已有项目怎么选餐 | 本 skill 怎么选餐 |
|---|---|
| `mcd-meal-brain`(14)、`mcd-solver`(10)：推荐「最划算」的组合 | 首推**复用上次**（`order-list`），命中则整个选餐环节消失 |
| 推荐类项目常给 5–10 个候选 | 硬性 ≤3 个，且价差 ≥5 元（实测存在 33.5/34/34.5 的无效三选一） |
| 不处理营销陷阱 | 剔除 `canWithOrder=true`（实测某店 8 个，标价需先购卡才成立） |
| `mcd-no-pickle`(17)：单个忌口 | 四道过滤：需购卡 / 多人餐 / 新品 / 非套餐 |

### 第 3 步 · 对一对 —— `query-meal-detail` 的下钻

**这是技术上最深的一层，也是榜单零覆盖的部分。**

128 个项目中，没有任何一个公开使用了 `query-meal-detail` 的 `rounds[].choices[].modification` 结构。本次实测拿到的是：

```jsonc
{
  "name": "精选单人餐三件套",
  "supportModify": false,              // ⚠️ 顶层 false
  "rounds": [{
    "choices": [{
      "code": "1406", "name": "板烧鸡腿堡",
      "supportModify": true,            // ✅ 真正的开关在这里
      "modification": {"items": [{
        "values": [
          {"name":"烤味酱",   "selectedKey":"0-1", "unselectedKey":"0-0"},
          {"name":"切块生菜", "selectedKey":"0-1", "unselectedKey":"0-0"}
        ]
      }]}
    }]
  }]
}
```

三条实操约束（传错就下单失败或配错餐）：

1. **顶层 `supportModify` 不可靠** —— 套餐常为 `false`，但配料为 `true`
2. **A 类组**（带 `unselectedKey`，如烤味酱/生菜）→ 该组**所有项都要传**，未选中传 `unselectedKey`
3. **B 类组**（不带 `unselectedKey`，如冰量四档）→ **只传选中项的 `selectedKey`**

映射到老年需求：

| 老年需求 | 落到哪个字段 | 是否加价 |
|---|---|:---:|
| 怕凉 / 牙敏感 → 少冰 | 饮料 modification「少冰」 | 免费 |
| 控血压 → 去酱 | 主食材 modification「烤味酱 / 巨无霸酱」 | 免费 |
| 牙口不好 → 去生菜 | 「切块生菜 / 生菜」 | 免费 |
| 控血糖 → 换无糖可乐 | choices `3071` 替换 | **+ ¥0** |
| 控糖（咖啡）→ 不加糖 | 「白砂糖」`selectedQuantity` 置 0 | 免费 |

**并且只给两个开关**（少冰、去酱）。给 20 项调整清单等于前两步白做——这是本 skill 与所有"功能型推荐"最本质的分歧：它主动舍弃能力。

---

## 四、主动放弃的能力（差异化的一部分）

| 放弃 | 理由 |
|---|---|
| 优惠最优组合 | 榜单 25+ 个项目在做；引入"要不要凑单"即新增决策点 |
| 新品首发 | 新品价高、口味不稳，不适合保守型用户 |
| 积分 / 抽奖 / 会员卡 | 任何营销动作都增加认知负荷 |
| 多门店对比 | 只给 1 家 |
| 营养疾病治疗 | 只保留高血压钠过滤（该人群患病率最高），其余不做医疗判定 |

这不是功能缺失，是设计取舍。

---

## 五、命名防撞检查

在 RANKING.md 全文检索以下关键词：

`a11y` / `accessible` / `accessibility` / `elder` / `elderly` / `senior` / `aging` / `无障碍` / `适老` / `老年` / `老人` / `爸妈` / `parents` / `read屏` / `screen-reader` / `caregiver`

结果：**全部 0 命中**。命名 `mcd-a11y-counter` 在榜单中唯一。

---

## 六、一句话总结

榜单的 128 个项目在回答「**点什么最划算 / 最健康 / 最好玩**」。

`mcd-a11y-counter` 在回答「**怎么让一个不擅长用智能手机的人，只用三次回答就能吃上饭**」。

前者优化的是结果质量，后者优化的是到达结果的成本。这是两条不相交的轴。
