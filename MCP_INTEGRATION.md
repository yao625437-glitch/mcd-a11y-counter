# MCP 集成说明

## 1. 使用的 MCP Server

| 项 | 值 |
|---|---|
| Server 名称 | `mcd-mcp` |
| 类型 | `streamablehttp` |
| 端点 | `https://mcp.mcd.cn` |
| 鉴权 | `Authorization: Bearer ${MCD_MCP_TOKEN}` |

配置文件见 [`mcp-config.example.json`](./mcp-config.example.json)，仅含环境变量占位符，不含任何真实凭证。

---

## 2. 调用的 Tool 清单

| # | Tool | 在适老链路中的作用 | 对应第几步 |
|---:|---|---|:---:|
| 1 | `now-time-info` | 取服务器权威时间（不用本地系统时间） | 1 |
| 2 | `query-nearby-stores` | `distance` → 走路分钟；`businessStartTime/EndTime` → 营业与打烊倒计时 | 1 |
| 3 | `delivery-query-addresses` | 模式 B：取收货地址 | 1 |
| 4 | `delivery-create-address` | 模式 B：无地址时新建 | 1 |
| 5 | `delivery-query-stores` | 模式 B：取可配送门店与 `beCode` | 1 |
| 6 | **`order-list`** | 复用上次订单 → 「还是来这个吗」，可跳过整个选餐环节 | 2 |
| 7 | `query-meals` | 取菜单，做四道过滤后收敛到 3 个套餐 | 2 |
| 8 | **`query-meal-detail`** | 下钻 `rounds[].choices[].modification` 做少冰/去酱等特调 | **3** |
| 9 | `list-nutrition-foods` | 用户提到高血压时，`sodium > 800mg` 保守过滤 | 2（条件） |
| 10 | `calculate-price` | 算价（需携带 `selectedKey`/`unselectedKey`） | 3 |
| 11 | `create-order` | 下单（两次确认后） | 3 |

**明确不调用**：`auto-bind-coupons`、`query-my-coupons`、`draw-lottery`、`mall-*`、`party-order-create`。
任何营销与加购动作都会增加决策点，与「降低认知负荷」的目标直接冲突。

---

## 3. 三步调用链路

```
第 1 步 · 定地方
  模式A  query-nearby-stores(beType=1, searchType=1)   # 收藏优先
          └ 无收藏 → searchType=2 + city + keyword
         now-time-info()                               # 校验营业与打烊倒计时
  模式B  delivery-query-addresses() → delivery-query-stores(beType=2, addressId)

第 2 步 · 定吃的
  order-list()                                        # 优先复用上次
   └ 空 → query-meals(storeCode, orderType, beType[, beCode])
           └ 四道过滤 → 三选一
  [条件] list-nutrition-foods()                       # 用户提到高血压时过滤钠

第 3 步 · 对一对
  query-meal-detail(storeCode, orderType, beType, code)
   └ 下钻 rounds[].choices[].modification
        ├ 少冰/去冰   → values.name = 少冰|去冰      (B 类，传 selectedKey)
        └ 去酱/去生菜 → values.name = 烤味酱|生菜     (A 类，未选中传 unselectedKey)
  calculate-price(...)  → 复述金额 → 第 2 次确认
  create-order(...)
  [模式B] 生成「给爸妈的一张卡」
```

---

## 4. 真实返回示例（2026-10-12 实测）

### 4.1 `query-nearby-stores` —— 第 1 步的全部依据

```json
{
  "storeCode": "1450713",
  "storeName": "麦当劳上海黄浦华旭国际大厦餐厅",
  "address": "南京东路街道西藏中路336号",
  "distance": 144,
  "businessStatus": true,
  "businessStartTime": "00:00",
  "businessEndTime": "23:59",
  "longitude": 0.0,
  "latitude": 0.0,
  "reservation": true,
  "reservationTimeOptions": [
    {"date": "2026-10-12", "today": true,
     "reservationOptionText": "夜市(17:14至21:45)，宵夜(22:14至23:59)"}
  ]
}
```

**同一区域另一家门店的营业时间完全不同**：`06:30 – 23:00`。深夜 / 清晨场景下 `businessStartTime`/`businessEndTime` 是决定性字段。

> ⚠️ `longitude` / `latitude` 实测恒为 `0.0`。本 skill 不使用门店坐标；也不需要，因为距离由 `distance` 直接提供。

> `reservationTimeOptions` 虽然提供了早餐/午餐/下午茶/夜市/宵夜的供餐时段，但**本 skill 刻意不展开**——引入"预约/时段"概念会额外增加决策点。

### 4.2 `query-meals` —— 第 2 步的降噪对象

实测某门店返回 **15 个分类**：

```
人气热卖 / 精选单人餐 / 鸡肉汉堡·卷 / 小食拼盘·多人餐 / 蘸酱炸鸡 / 随心配1+1
/ 大堡口福 / 巨无霸牛鱼肉堡 / 安格斯MAX / 炸鸡 / 小食甜品·其他
/ 开心乐园 / 麦咖啡™ / 500大卡套餐 / 饮品
```

其中需额外购卡才享标价的商品（**老年用户的隐性陷阱**）：

```json
"9900004236": {
  "name": "人气超值四件套随心选",
  "currentPrice": "28",
  "originalPrice": "57",
  "discountType": "随单购麦金卡优惠",
  "withOrder": {"membershipCode": "106", "specId": "880"},
  "canWithOrder": true
}
```

标价 28 元，**不买麦金卡就享受不到这个价**。实测该店有 8 个此类商品。第 2 步的过滤规则 1 直接剔除全部。

### 4.3 `query-meal-detail` —— 第 3 步的核心（完整三级结构）

`精选单人餐三件套`（code `9900004064`）实测：

```jsonc
{
  "code": "9900004064",
  "name": "精选单人餐三件套",
  "supportModify": false,              // ⚠️ 顶层是 false

  "rounds": [
    {
      "id": 1, "name": "主食任意选", "minQuantity": 1, "maxQuantity": 1,
      "choices": [
        {
          "code": "1406", "name": "板烧鸡腿堡",
          "isDefault": 1, "diffPrice": "+ ¥0",
          "supportModify": true,        // ✅ 真正的判断依据在这里
          "modification": {"items": [{
            "maxValues": 2, "minValues": 0,
            "values": [
              {"code":"102201","name":"烤味酱","price":0,
               "selectedQuantity":1,"selectedKey":"0-1","unselectedKey":"0-0"},
              {"code":"120512","name":"切块生菜","price":0,
               "selectedQuantity":1,"selectedKey":"0-1","unselectedKey":"0-0"}
            ]
          }]}
        },
        {"code":"1100","name":"巨无霸","isDefault":0,"diffPrice":"+ ¥2",
         "supportModify":true,
         "modification":{"items":[{"maxValues":5,"minValues":0,"values":[
            {"code":"100116","name":"巨无霸酱","unselectedKey":"0-0"},
            {"code":"100141","name":"吉士","unselectedKey":"0-0"},
            {"code":"100168","name":"生菜","unselectedKey":"0-0"},
            {"code":"100202","name":"酸黄瓜","unselectedKey":"0-0"},
            {"code":"100212","name":"洋葱粒","unselectedKey":"0-0"}
         ]}]}}
      ]
    },
    {
      "id": 2, "name": "选择套餐内小食",
      "choices": [
        {"code":"4810","name":"中薯条","isDefault":1,"diffPrice":"+ ¥0","supportModify":false},
        {"code":"4437","name":"小杯玉米杯","isDefault":0,"diffPrice":"- ¥0.5","supportModify":false}
      ]                                  // ⚠️ 小食轮次全部不可改
    },
    {
      "id": 3, "name": "选择套餐内饮料",
      "choices": [
        {"code":"3050","name":"可乐中杯","isDefault":1,"diffPrice":"+ ¥0","supportModify":true,
         "modification":{"items":[{"maxValues":1,"minValues":1,"values":[
            {"code":"200002","name":"标准","selectedQuantity":1,"selectedKey":"0-1"},
            {"code":"200002","name":"去冰","selectedQuantity":0,"selectedKey":"0-0"},
            {"code":"200002","name":"多冰","selectedQuantity":0,"selectedKey":"0-2"},
            {"code":"200002","name":"少冰","selectedQuantity":0,"selectedKey":"1-1"}
         ]}]}},                          // ⚠️ 没有 unselectedKey → B 类
        {"code":"3071","name":"无糖可口可乐中杯","isDefault":0,
         "diffPrice":"+ ¥0","supportModify":true},   // 🎯 换无糖不加钱
        {"code":"520688","name":"大杯鲜萃咖啡","diffPrice":"+ ¥1.5","supportModify":true,
         "modification":{"items":[{"maxValues":2,"minValues":0,"values":[
            {"code":"120519","name":"奶油球","unselectedKey":"0-0"},
            {"code":"120520","name":"白砂糖","unselectedKey":"0-0"}
         ]}]}}
      ]
    }
  ]
}
```

完整的老年友好映射表、A/B 两类传参规则、`selectedKey`/`unselectedKey` 用法见
[`references/modification-guide.md`](./references/modification-guide.md)。

### 4.4 `order-list` —— 实测为空

```json
{"success":true,"code":200,"message":"请求成功","data":{}}
```

返回的是**空对象 `{}`**，不是空数组 `[]`。这是新账号 / 无历史订单时的常态，不是错误。

本 skill 的处理：**静默降级到菜单收敛，不告诉用户"没有历史订单"**。
（让一个老人听到"您没有历史订单"是纯粹的信息噪音。）

有订单时的结构：

```
data.list[].orderId / storeName / createTime / realTotalAmount
         └ orderProductList[].productCode / productName / quantity
              └ comboItemList[]
```

### 4.5 `now-time-info`

```json
{"date":"2026-10-12","datetime":"2026-10-12T17:49:03.922",
 "dayOfWeek":"MONDAY","timezone":"GMT+08:00"}
```

### 4.6 `delivery-query-addresses` —— 实测为空

```json
{"data":{"addresses":[]}}
```

模式 B 时必须处理这个情况，引导 `delivery-create-address` 新建。

### 4.7 `delivery-create-address` —— 字段规范（模式 B 的必经之路）

必填五项，`gender` 选填：

| 字段 | 必填 | 规范 | 示例 |
|---|:---:|---|---|
| `city` | ✅ | 城市名称，**要带「市」** | `"南京市"` |
| `contactName` | ✅ | 联系人姓名 | `"李明"` |
| `phone` | ✅ | **11 位纯数字，以 1 开头** | `"1XXXXXXXXXX"`（示意格式，非真实号码） |
| `address` | ✅ | 配送地址（**不含门牌号**） | `"清竹园9号楼"` |
| `addressDetail` | ✅ | 门牌号（**单独一个字段**） | `"2单元508"` |
| `gender` | ⚪ | 填的是 **`"先生"` / `"女士"`**，不是 male/female | `"先生"` |

⚠️ 两个易错点：

1. **`address` 与 `addressDetail` 是拆开的两个字段**。把「XX小区9号楼2单元508」整串塞进 `address` 是不符合设计意图的。
2. **`gender` 选填**。适老化流程里如果老人/子女没有说性别，**不要追问**，直接不传。

> 本 skill 的立场：**不用示例数据去向真实账号写地址**。这会污染用户的地址簿，而用户还得去 App 里删。
> 缺地址时的正确做法是照着上面的字段表，一次向用户问清。

### 4.8 `calculate-price` —— 实跑通过

请求 1（板烧 + 去酱 + 中薯条 + 可乐少冰）：

```jsonc
{"storeCode":"1450713","orderType":1,"beType":1,
 "items":[{"productCode":"9900004064","quantity":1,"roundList":[
   {"round":"1","comboItemList":[{"code":"1406","quantity":1,
     "modification":{"values":[
       {"code":"102201","key":"0-0","quantity":0},     // 去酱 → unselectedKey，份数 0
       {"code":"120512","key":"0-1","quantity":1}]}]},  // 留生菜 → selectedKey，份数 1
   {"round":"2","comboItemList":[{"code":"4810","quantity":1}]},
   {"round":"3","comboItemList":[{"code":"3050","quantity":1,
     "modification":{"values":[{"code":"200002","key":"1-1","quantity":1}]}]}  // 少冰
 ]}]}
```

返回：`{"price":3450,"originalPrice":3450,"discount":0}` → **34 元 5 角**

请求 2：仅把 round 3 的 `code` 换成 `3071`（无糖可乐），其余不变 → `price` 仍为 **3450**。
✅ **换无糖可乐零差价，实证成立。**

**价格字段单位一律是分**（`enjoyed.realDiscount` 例外，是元）。展示前 ÷100。

**意外收获 —— `takeWayList`**：

```json
"takeWayList":[
  {"code":"eat-in","title":"堂食","subtitle":"店内用餐"},
  {"code":"locker-out","title":"外带","subtitle":"店外取餐柜"}]
```

工具定义写明 code「到店下单时需要携带」→ **模式 A 下单前必须让用户选堂食/外带**并传 code。漏传会下单失败。

### 4.9 深圳真实地址跑通模式 B（2026-10-12）

| 步骤 | 调用 | 结果 |
|---|---|---|
| 1 | `delivery-query-addresses()` | `{"addresses":[]}` —— 账号无地址 |
| 2 | `delivery-create-address(city="[城市]", contactName="[姓名]", gender="女士", phone="[11位手机号]", address="[区][小区]10区3栋", addressDetail="902")` | ✅ 返回 `addressId`；`fullAddress` 被系统规范化（**自动补全街道与门牌前缀**） |
| 3 | `delivery-query-stores(beType=2, addressId)` | 3 家可配送：同小区门店 `1421184`/`142118402`、另两家 `1420462`、`1420629`（后两家为 24 小时） |
| 4 | `query-meals(1421184, orderType=2, beType=2, beCode=142118402)` | 外送菜单，13 个分类 |
| 5 | `query-meal-detail(9900003004)` | 见下 |
| 6 | `calculate-price(...)` | `price: 3890` → **38 元 9 角** |

算价返回拆解：

```json
{"productPrice":3100, "deliveryPrice":600, "packingPrice":190,
 "price":3890, "discount":0}
```

| 项 | 分 | 元 |
|---|---:|---:|
| 商品（麦乐鸡5块中套餐） | 3100 | 31.00 |
| 配送费 | 600 | 6.00 |
| 打包费 | 190 | 1.90 |
| **实付** | **3890** | **38.90** |

→ **比商品标价贵 25%**，模式 B 必须向用户披露这个构成。

另外 `productList` 里会额外出现一项 `920174 打包服务费`（`quantity: 19`，`subtotal: 0`）——
它是系统内部项，**不要念给用户听**，只按上表四行说。

---

| MCP 字段 | 无障碍用途 | 处理方式 |
|---|---|---|
| `distance` | 判断走路远近 | `a11y_format.py walk`（老年步速 50 m/min） |
| `businessStartTime` / `businessEndTime` | 营业判定、打烊倒计时 | `a11y_format.py open`（支持跨夜） |
| `storeName` / `address` | 第 1 步呈现 | 四段式短句 |
| `storeCode` / `beCode` | 下单参数 | **不向用户展示** |
| `canWithOrder` | 隐性陷阱识别 | `true` 一律剔除 |
| `tags` | 新品 / 套餐识别 | 「上新」剔除、「套餐」优先 |
| `currentPrice` | 价格排序与三选一 | `a11y_format.py money` |
| `orderProductList[].productName` | 复用上次订单 | 「上次您点的是 XX」 |
| `supportModify`（**choices 层**） | 能否调整 | 下钻判断，顶层不可靠 |
| `diffPrice` | 换选项的差价（元字符串） | 优先推荐 `+ ¥0` 的 |
| `values[].price` | 单项加价（**单位分**） | 与 `diffPrice` 单位不同，勿混 |
| `selectedKey` / `unselectedKey` | 特调传参 | A/B 两类规则不同 |
| `sodium`（`list-nutrition-foods`） | 高血压保守过滤 | > 800mg 剔除 |

---

## 6. 本次开发实测发现的十四个事实（已固化进 SKILL.md）

| # | 发现 | 影响 |
|---:|---|---|
| 1 | 套餐顶层 `supportModify` 实测为 `false`，但配料的 `choices[].supportModify` 为 `true` | 只用顶层字段判断会得出完全错误的"改不了"结论 |
| 2 | 含 `unselectedKey` 的特调组**所有项都要传**（未选中传 `unselectedKey`） | 少传会配错餐 |
| 3 | 冰量组**没有** `unselectedKey`，只传选中项的 `selectedKey` | 当 A 类处理会出错 |
| 4 | 换**无糖可口可乐** `diffPrice = + ¥0`，**已用 `calculate-price` 实证**（3450 → 3450） | 控糖老人换无糖不加钱，可当默认动作 |
| 5 | `diffPrice` 是「元」字符串，`values[].price` 是「分」整数 | 两套单位，混淆会算错钱 |
| 6 | `order-list`、`delivery-query-addresses` 实测均返回**空** | 无历史/无地址是常态，必须有静默降级路径 |
| 7 | `roundList[].round` 填的是 `rounds[].id` 的**字符串形式**（`"1"`），不是 name | 填 name 会算价失败 |
| 8 | `modification.values[]` 里 **`key` 决定状态、`quantity` 决定份数**，两者都要给 | 去掉一项要写成 `{key: unselectedKey, quantity: 0}` |
| 9 | `calculate-price` 返回价格**单位是分**（`enjoyed.realDiscount` 例外，是元） | 不 ÷100 会把 34.5 元显示成 3450 元 |
| 10 | 到店场景返回 **`takeWayList`**（`eat-in` 堂食 / `locker-out` 外带），下单需携带 code | 漏传下单失败 |
| 11 | `delivery-create-address` 的 `address` 与 `addressDetail` **是两个字段**；`gender` 选填且填「先生/女士」 | 合并填不合规范；性别一律不追问 |
| 12 | **外送与到店是两套 code、两套价**（板烧 `1406`/23.5 → 外送 `901406`/26；可乐 `3050` → `903050`） | 换模式必须重新查菜单与详情，不能复用 code |
| 13 | **外送有配送费 + 打包费**（实测 +6.00 +1.90，比标价贵 25%） | 复述卡只报商品价会让父母以为被多收钱，必须拆开说 |
| 14 | **「去酱」开关不是所有套餐都有** —— `麦乐鸡(5块)中套餐` 的 round1(主食)、round2(小食) 均 `supportModify=false` | 写死"两个开关"会对用户承诺做不到的事；必须先查再给 |

---

## 7. 辅助脚本

`scripts/a11y_format.py`（仅标准库）提供三项换算，已验证：

```
$ python a11y_format.py demo
34.5        ->  34 元 5 角
144 米      ->  走路 3 分钟就到
1200 米     ->  走路要 24 分钟，太远了。要不要改成送到家？   [建议改外送]
23:00       ->  晚上 11 点
18:00-06:00 ->  现在开门，到早上 6 点      （跨夜门店判定正确）
06:00-21:00 ->  这家店再有 14 分钟就关门了，可能来不及。要不要换一家，或者送到家？
```

---

## 8. 业务价值

| 对象 | 痛点 | 本 skill 的解法 |
|---|---|---|
| 老年用户 | 15 个分类、约 110 个 SKU 无从下手 | 三步流程，每步 ≤3 选项，全是否式确认 |
| 读屏软件用户 | 表格、¥ 符号、24 小时制无法正确朗读 | 纯文本短行 + 「元/角」+ 口语时刻 |
| 子女 | 想给父母点，但父母不会操作 App | 模式 B：子女全程代决策，父母只负责收 |
| 有健康限制的老人 | 不知道哪个咸、哪个甜 | 默认少冰去酱，控糖换无糖（0 差价），高血压过滤钠 |
| 麦当劳 | 老年客群在数字化点餐中被系统性排除 | 提供低认知负荷通道 |

**主动放弃的能力**（有意为之，非缺失）：优惠最优组合、品类最全、新品最先、积分与抽奖、品牌会员卡。每一项都会引入决策点。

---

## 9. 合规与安全

- **不下单前两次确认、不复述金额，绝不调用 `create-order`**
- 涉及真实资金，任何失败都不能重试下单；失败一律回到第 3 步让用户重新确认
- 默认健康偏好（少冰 / 去酱 / 换无糖）仅为保守过滤，**不构成医疗建议**
- 「给爸妈的一张卡」只含必要收餐信息，不含订单号、手机号、支付凭证
- 配置文件仅 `${MCD_MCP_TOKEN}` 占位符，仓库中不含任何真实凭证
