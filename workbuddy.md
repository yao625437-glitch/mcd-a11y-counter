# workbuddy.md · 使用 WorkBuddy 开发的对话上下文

> 本文件用于核验「WorkBuddy 专项奖励」资格。
> 内容由腾讯 WorkBuddy 会话导出，记录本项目的完整开发过程。

---

## 一、项目信息

| 项 | 值 |
|---|---|
| 项目名称 | mcd-a11y-counter · 麦当劳适老与无障碍点餐台 |
| 一句话定位 | 整个点餐过程只有三步，每一步一次提问、一次回答、一个是否式确认 |
| 开发工具 | **腾讯 WorkBuddy**（Windows，中文环境） |
| MCP Server | `mcd-mcp`（`https://mcp.mcd.cn`，streamablehttp） |
| 辅助脚本 | `scripts/a11y_format.py`（Python 标准库，已实跑验证） |
| 开发日期 | 2026-10-12 |
| 参赛赛事 | 麦当劳程序员创意开发大赛（M-China/mcd-developer-innovation-challenge） |

---

## 二、开发对话上下文（按时间顺序）

### 第 1 轮 · 需求与差异化定位

**用户**：基于 `M-China/mcd-developer-innovation-challenge` 的要求，用 mcd-mcp 设计五个不同的 skill，注意与 RANKING.md 已有的 skill 作出区分。

**WorkBuddy 的处理**：

1. 拉取仓库 `README.md`、`activityGuidelines.md`、`RANKING.md`，确认赛事规则与硬性文件要求
2. 对 RANKING.md 的 128 个上榜项目做语义聚类，统计赛道拥挤度
3. **实际调用 mcd-mcp 验证能力**，而不是凭工具定义推测：
   - `query-nearby-stores` → 拿到 `distance` / `businessStartTime` / `businessEndTime` / `reservationTimeOptions`
   - `list-nutrition-foods` → 拿到 160 条营养数据（含 `sodium`、`carbohydrate`）
   - `now-time-info`、`query-my-account`、`campaign-calendar`、`delivery-query-addresses`
4. 识别出五个零占用赛道，各出一个方案

**结论**：五个零占用赛道 = 企业团餐 / 临床营养 / 适老无障碍 / 天气环境 / 内容生成

### 第 2 轮 · 收敛为单 skill 主推

**用户**：主推 `mcd-a11y-counter` 三步决策 + 子女代下单卡片 + 门店距离/营业时段 + `query-meal-detail` 特调，删除其他 skill，充分思考、确认补足并丰富内容。

**WorkBuddy 的处理**：

1. 删除其余四个 skill 目录（企业团餐 / 临床营养 / 天气环境 / 内容生成）
2. 临床营养的高血压钠过滤能力并入本 skill 第 2 步的条件过滤（老年人群高血压患病率本就最高）
3. 再次深挖 mcd-mcp：
   - `query-meal-detail(code=9900004064)` → 拿到完整三级结构 `rounds → choices → modification → items → values`
   - `order-list` → 确认空返回是 `{"data":{}}`
4. 重写 SKILL.md，新增两份 references 手册与一个格式化脚本

**关键修正**：实测发现套餐**顶层 `supportModify` 是 `false`**，而配料的 `choices[].supportModify` 是 `true` —— 原先用顶层字段判断"能不能改"是错的。

### 第 3 轮 · 真实账号验证

**用户**：用我自己的账号跑一遍模式 B。

**WorkBuddy 的处理**：

1. `delivery-query-addresses` → 返回 `{"addresses":[]}`
2. 取 `delivery-create-address` 与 `calculate-price` 的完整 schema
3. **判断**：不用示例数据向真实账号写地址（会污染地址簿）
4. 改用不依赖地址的方式验证最关键的一环 —— 用 `calculate-price` 实跑，验证 `selectedKey`/`unselectedKey` 传参规则

**实跑结果**：`price: 3450`（34 元 5 角），传参规则全部成立；换无糖可乐后仍是 3450，**零差价实证成立**。
**意外发现**：返回里有 `takeWayList`，到店下单需携带 code —— 此前完全未覆盖。

### 第 4 轮 · 深圳真实地址跑通

**用户**：提供深圳市某收货地址（真实信息）。

**WorkBuddy 的处理**（完整链路）：

| 步 | 调用 | 结果 |
|---:|---|---|
| 1 | `delivery-query-addresses` | 空 |
| 2 | `delivery-create-address` | ✅ 建成功，`fullAddress` 被系统自动补全街道与门牌前缀 |
| 3 | `delivery-query-stores(beType=2)` | 3 家可配送，选同小区门店 |
| 4 | `query-meals` | 外送菜单 13 个分类 |
| 5 | 四道过滤 → 三选一 | 麦乐鸡套餐 31 / 酥酥多笋卷套餐 39 / 巨无霸套餐 44 |
| 6 | `query-meal-detail` | 见下方 |
| 7 | `calculate-price` | ✅ `price: 3890` → **38 元 9 角** |

**在 `create-order` 前停下** —— 涉及真实资金，按设计需两次确认，不自动下单。

**三个实测意外**：
- 外送与到店是两套 code、两套价（板烧 `1406`/23.5 → 外送 `901406`/26）
- 外送实付比标价贵 25%（31 + 配送 6 + 打包 1.9 = 38.9）
- 炸鸡类套餐没有"去酱"（主食与小食均 `supportModify=false`）—— 原写死的两个开关是错的

### 第 5 轮 · 提交整理

**用户**：按投稿要求，再次确认无敏感信息遗漏后，整理为可直接提交的文件格式。

**WorkBuddy 的处理**：
1. 六类敏感信息全量扫描（手机号 / Token / 姓名地址 / 本机路径 / 邮箱 / 订单号）
2. 修复三处残留（示例手机号、区级地名、本机用户名路径）
3. 整理为「仓库根即可提交」的结构
4. 生成本文件

---

## 三、实际使用的 mcd-mcp Tool

| Tool | 用途 |
|---|---|
| `now-time-info` | 取服务器权威时间，做营业与打烊倒计时校验 |
| `query-nearby-stores` | 模式 A：`distance` 换走路分钟、`businessStartTime/EndTime` 做营业校验 |
| `delivery-query-addresses` | 模式 B：取收货地址 |
| `delivery-create-address` | 模式 B：无地址时新建 |
| `delivery-query-stores` | 模式 B：取可配送门店与 `beCode` |
| `order-list` | 第 2 步优先复用上次订单 |
| `query-meals` | 第 2 步：四道过滤后收敛到 3 个套餐 |
| `query-meal-detail` | 第 3 步：下钻 `rounds[].choices[].modification` 做特调 |
| `list-nutrition-foods` | 用户提到高血压时按 `sodium > 800mg` 保守过滤 |
| `calculate-price` | 算价（携带 `selectedKey`/`unselectedKey`） |
| `create-order` | 下单（**仅设计，本次未真实调用**） |

**明确不调用**：`auto-bind-coupons`、`query-my-coupons`、`available-coupons`、`draw-lottery`、`mall-*`、`party-order-create`。
任何营销与加购动作都会增加老年用户的决策点，与目标直接冲突。

---

## 四、实测关键数据

**1. 外送算价（深圳，模式 B）**

```json
{"productPrice":3100, "deliveryPrice":600, "packingPrice":190,
 "price":3890, "discount":0}
```

**2. 到店算价（上海，模式 A）**

```json
{"price":3450, "originalPrice":3450, "discount":0}
```

把 round 3 的饮料 code 从 `3050`（可乐）换成 `3071`（无糖可乐），`price` 仍为 3450 —— **零差价实证成立**。

**3. 特调三级结构**

```jsonc
{"supportModify": false,              // ⚠️ 顶层 false
 "rounds":[{"choices":[
   {"code":"1406","name":"板烧鸡腿堡","supportModify":true,   // ✅ 真正的开关在这里
    "modification":{"items":[{"values":[
      {"name":"烤味酱","selectedKey":"0-1","unselectedKey":"0-0"}]}]}}]}]}
```

**4. 需购卡商品的误导结构**

```json
{"name":"人气超值四件套随心选","currentPrice":"28","originalPrice":"57",
 "discountType":"随单购麦金卡优惠","canWithOrder":true}
```

标价 28 元，**不买卡享受不到** —— 第 2 步过滤规则 1 直接剔除。

**5. 空数据是常态**

```
order-list                → {"data":{}}
delivery-query-addresses  → {"data":{"addresses":[]}}
```

---

## 五、WorkBuddy 在本项目中的具体作用

| 环节 | WorkBuddy 做了什么 |
|---|---|
| 创意定位 | 拉取并解析 RANKING.md 128 个项目，聚类出赛道拥挤度，定位零占用方向 |
| 能力验证 | 实际调用 mcd-mcp 十余个工具，用真实返回而非文档推测来设计 |
| 缺陷发现 | 三轮实跑累计发现 14 个文档/设计缺陷并全部修正 |
| 代码编写 | 编写并测试 `scripts/a11y_format.py`（金额/距离/营业时段换算） |
| 文档生成 | 生成 SKILL.md、README.md、MCP_INTEGRATION.md 及两份 references 手册 |
| 合规把关 | 六类敏感信息扫描，修复示例手机号、区级地名、本机路径三处残留 |
| 提交整理 | 整理为仓库根即可提交的结构，生成报名材料 |

---

## 六、产出文件

```
mcd-a11y-counter/                       ← 直接作为 GitHub 仓库根
├── README.md                           必须：项目介绍、安装、使用示例、目标用户
├── CONTEST_DECLARATION.md              必须：参赛声明（官方原文，未改动）
├── MCP_INTEGRATION.md                  必须：MCP Server / Tool / 流程 / 业务价值
├── SKILL.md                            源代码：三步决策 + 十二条无障碍规约
├── scripts/a11y_format.py              源代码：可运行的格式化脚本（已验证）
├── references/modification-guide.md    源代码：特调三级下钻手册
├── references/output-templates.md      源代码：适老化话术库
├── mcp-config.example.json             必须：脱敏配置，仅环境变量占位符
├── DIFFERENTIATION.md                  可选：与 128 个上榜项目的差异化分析
└── workbuddy.md                        本文件：WorkBuddy 专项奖励凭证
```

---

## 七、声明

- 本项目**全程使用腾讯 WorkBuddy** 完成创意构思、能力验证、代码编写、文档生成与合规检查
- 仓库中**不含任何真实 Token、密钥、账号凭证**
- 仓库中**不含任何真实个人信息**（姓名、手机号、住址一律使用占位符）
- 输出不构成医疗建议；餐品、价格、门店状态以麦当劳官方渠道实时结果为准
