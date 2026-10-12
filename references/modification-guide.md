# 特调下钻手册（基于 2026-10-12 真实返回）

适用对象：`query-meal-detail` 的返回结构解析。
样例商品：`精选单人餐三件套`（code `9900004064`，门店 `1450713`，`orderType=1, beType=1`）。

---

## 一、结论先行：三个最容易做错的地方

| # | 常见错误做法 | 正确做法 |
|---:|---|---|
| 1 | 用**顶层** `supportModify` 判断"能不能改" | 必须下钻到 `rounds[].choices[].supportModify` |
| 2 | 只把**选中的**那一项传给算价/下单 | 含 `unselectedKey` 的组，**该组所有项都要传**（选中传 `selectedKey`，未选中传 `unselectedKey`） |
| 3 | 认为所有特调组都是"多选增减" | 分 A/B 两类，传参规则不同（见 §四） |

---

## 二、真实结构

```jsonc
{
  "code": "9900004064",
  "name": "精选单人餐三件套",
  "supportModify": false,          // ⚠️ 顶层是 false！但套餐里到处都能改

  "rounds": [
    {
      "id": 1,
      "name": "主食任意选",
      "quantity": 1, "maxQuantity": 1, "minQuantity": 1,
      "choices": [
        {
          "code": "1406",
          "name": "板烧鸡腿堡",
          "quantity": 1,
          "isDefault": 1,                 // 1 = 当前默认选中
          "diffPrice": "+ ¥0",            // 换这个的差价（字符串，单位元）
          "supportModify": true,          // ✅ 这一项能改
          "modification": {
            "items": [{
              "maxValues": 2, "minValues": 0,
              "values": [
                {"code":"102201","price":0,"name":"烤味酱",
                 "maxQuantity":1,"minQuantity":0,
                 "selectedQuantity":1,
                 "selectedKey":"0-1", "unselectedKey":"0-0"},   // ← 有 unselectedKey
                {"code":"120512","price":0,"name":"切块生菜",
                 "selectedQuantity":1,
                 "selectedKey":"0-1", "unselectedKey":"0-0"}
              ]
            }]
          }
        }
      ]
    },
    {
      "id": 2,
      "name": "选择套餐内小食",
      "choices": [
        {"code":"4810","name":"中薯条","isDefault":1,"diffPrice":"+ ¥0","supportModify":false},
        {"code":"4437","name":"小杯玉米杯","isDefault":0,"diffPrice":"- ¥0.5","supportModify":false}
      ]
      // ⚠️ 小食轮次实测全部 supportModify=false —— 薯条/玉米杯改不了
    },
    {
      "id": 3,
      "name": "选择套餐内饮料",
      "choices": [
        {"code":"3050","name":"可乐中杯","isDefault":1,"diffPrice":"+ ¥0","supportModify":true,
         "modification":{"items":[{
            "maxValues":1,"minValues":1,                        // 必选一项
            "values":[
              {"code":"200002","name":"标准","selectedQuantity":1,"selectedKey":"0-1"},
              {"code":"200002","name":"去冰","selectedQuantity":0,"selectedKey":"0-0"},
              {"code":"200002","name":"多冰","selectedQuantity":0,"selectedKey":"0-2"},
              {"code":"200002","name":"少冰","selectedQuantity":0,"selectedKey":"1-1"}
            ]                                                    // ← 没有 unselectedKey
         }]}}
      ]
    }
  ]
}
```

### 关键字段

| 字段 | 位置 | 含义 |
|---|---|---|
| `supportModify` | 顶层 | 整个商品能否改 —— **不可靠，套餐常为 false** |
| `supportModify` | `choices[]` | 该可选项能否改 —— **判断依据在这里** |
| `isDefault` | `choices[]` | 1 = 当前默认搭配 |
| `diffPrice` | `choices[]` | 换选项的差价，**字符串、单位元**（`"+ ¥2"` / `"- ¥0.5"`） |
| `modification.items[]` | `choices[]` 内 | 一组相关的可调整项 |
| `maxValues` / `minValues` | `items[]` | 该组最多/最少选几项 |
| `selectedQuantity` | `values[]` | 当前是否已选（1 = 已选） |
| `price` | `values[]` | **整数、单位分**（`"price":500` = 5 元）⚠️ 与 `diffPrice` 单位不同 |
| `selectedKey` | `values[]` | 选中时传给算价/下单 |
| `unselectedKey` | `values[]` | 存在时表示"这一项可以不选"，未选中要传它 |

---

## 三、传参规则（硬性）

### A 类：含 `unselectedKey` 的组（多选增减型）—— 主食配料属于这类

工具定义原文：

> 选中的特调项：将 `selectedKey` 传给 `calculate-price` 和 `create-order`
> 未选中的特调项：将 `unselectedKey` 传给 `calculate-price` 和 `create-order`
> 即：**该组内所有特调项都需要传入**，选中的用 `selectedKey`，未选中的用 `unselectedKey`

**示例**：板烧鸡腿堡，要去酱、留生菜

```
烤味酱   （未选中）→ 传 "0-0"
切块生菜 （选中）  → 传 "0-1"
```

两项都要传，缺一项会导致该组配置错乱。

### B 类：不含 `unselectedKey` 的组（单选互斥型）—— 冰量属于这类

四个选项 `code` 全是 `200002`，靠 key 区分。**只传选中那一项的 `selectedKey`**，其余不传。

```
少冰 → 传 "1-1"    （不要传 标准/去冰/多冰）
去冰 → 传 "0-0"
```

**把 B 类当 A 类传会出错。**

### 判别方法

```
组内有任何 value 带 unselectedKey 且该字段非空  →  A 类
否则                                            →  B 类
```

### 两个例外

1. `minValues=1 且 maxValues=1 且 values 只有 1 项` → **必选**，不得向用户提供"不选"
2. `maxValues=0 且 minValues=0 且 values=[]` → **空组**，直接忽略（实测 `热浓浓黑巧中杯` 有这样的组）

---

## 四、老年友好特调映射表（全部来自实测）

### 4.1 换选项（走 `choices[].diffPrice`）

| 老年需求 | 换成 | code | diffPrice | 说明 |
|---|---|---|:---:|---|
| **控血糖 / 别太甜** | 无糖可口可乐中杯 | `3071` | **+ ¥0** | 🎯 **不加钱，可当默认动作** |
| 不要碳酸 / 清爽 | 阳光柠檬红茶中杯 | `515281` | + ¥0 | 同样不加钱 |
| 不要可乐味 | 雪碧中杯 | `3060` | + ¥0 | 同样不加钱 |
| 少吃油炸 | 小杯玉米杯 | `4437` | **- ¥0.5** | 换掉中薯条还能便宜 5 角 |
| 想喝点热的 | 热浓浓黑巧中杯 | `515945` | + ¥11 | 偏贵，需提示价格变化 |
| 补充营养 | 纯牛奶 | `3755` | + ¥0.5 | `supportModify=false` |

### 4.2 改配料（走 `modification.values` 的 key）

**怕凉、牙敏感**

| 动作 | 所属 choice | values.name | 传参 |
|---|---|---|---|
| 少冰 | 任意支持冰量的饮料 | `少冰` | selectedKey `"1-1"`（B 类，只传这项） |
| 去冰 | 同上 | `去冰` | selectedKey `"0-0"` |
| 多冰 | 同上 | `多冰` | selectedKey `"0-2"` |

**控血压 / 少盐（酱料是钠的主要来源）**

| 动作 | 主食材 choice | values.name / code | 传参（A 类） |
|---|---|---|---|
| 去酱 | 板烧鸡腿堡 `1406` | 烤味酱 `102201` | 未选中 → `"0-0"` |
| 去酱 | 巨无霸 `1100` | 巨无霸酱 `100116` | 未选中 → `"0-0"` |
| 去酱 | 麦辣鸡腿汉堡 `1440` | 麦香鸡酱 `100136` | 未选中 → `"0-0"` |
| 去酱 | 深海鳕鱼堡 `520312` | 麦香鱼酱 `100126` | 未选中 → `"0-0"` |
| 去酱 | 培根安格斯厚牛堡 `511781` | 烤牛肉风味酱 `100179` | 未选中 → `"0-0"` |

**牙口不好 / 咀嚼困难**

| 动作 | choice | values.name / code | 传参 |
|---|---|---|---|
| 去生菜 | 板烧鸡腿堡 `1406` | 切块生菜 `120512` | 未选中 → `"0-0"` |
| 去生菜 | 巨无霸 `1100` | 生菜 `100168` | 未选中 → `"0-0"` |

**忌口**

| 动作 | choice | values.name / code | 传参 |
|---|---|---|---|
| 去酸黄瓜 | 巨无霸 `1100` | 酸黄瓜 `100202` | 未选中 → `"0-0"` |
| 去洋葱 | 巨无霸 `1100` | 洋葱粒 `100212` | 未选中 → `"0-0"` |
| 去芝士 | 巨无霸 `1100` / 鳕鱼堡 `520312` / 安格斯 `511781` | 吉士 `100141` | 未选中 → `"0-0"` |
| 去培根 | 培根安格斯厚牛堡 `511781` | 培根 `103386` | 未选中 → `"0-0"` |
| 去黄油 | 培根安格斯厚牛堡 `511781` | 黄油 `120160` | 未选中 → `"0-0"` |

**控糖（咖啡类）**

| 动作 | choice | values.name / code | 传参 |
|---|---|---|---|
| 不加糖 | 大杯鲜萃咖啡 `520688` | 白砂糖 `120520` | 未选中 → `"0-0"` |
| 不加奶精 | 大杯鲜萃咖啡 `520688` | 奶油球 `120519` | 未选中 → `"0-0"` |
| 不加糖浆 | 冰美式 `507411` / 冰奶铁 `507409` / 热美式 `507368` / 热奶铁 `507328` | `加`（code `8008`，**price 500 = 5 元**） | 选 `不加` → `"0-0"` |

> ⚠️ 最后一行的 `加` 项 `price=500` 单位是**分**（5 元）。与 `choices[].diffPrice` 的「元字符串」是两套单位，别混。

### 4.3 实测改不了的部分

| 轮次 | 项目 | supportModify |
|---|---|:---:|
| 选择套餐内小食 | 中薯条 / 大薯条 / 小杯玉米杯 / 大杯玉米杯 / 扭扭薯 / 心形薯饼 | **false** |
| 选择套餐内饮料 | 纯牛奶 `3755` / 锡兰红茶 `3505` / 100%苹果汁 `6362` / 香草奶昔 `521588` / 草莓奶昔 `521589` / 热浓浓燕麦黑巧 `515954` | **false** |

**小食轮次整体不可改**。这意味着「薯条少放盐」这类请求在系统里做不到。

此时的正确话术（区分"系统里做不到"与"门店做不到"）：

```
这个在系统里改不了。
您到柜台的时候可以跟店员说一声。
```

**不要说「改不了」就结束** —— MCP 不支持 ≠ 门店不能做。

---

## 五、插入到流程里的位置

在第 3 步（确认）里，且**只给两个开关**：

```
要不要让店里少放点冰？        → 饮料 modification 的「少冰」
要不要让店里别放酱？          → 主食材 modification 的「烤味酱」
```

其余 §4 的项，**用户提了才做**，不主动罗列。把 20 项调整摊开给老人看 = 前两级降噪白做了。

---

## 六、算价传参实证（2026-10-12 真实调用通过）

### 6.1 `roundList` 结构

`round` 字段填的是 `rounds[].id` 的**字符串形式**（`"1"` / `"2"` / `"3"`），**不是 name**。

已跑通的完整请求（`storeCode=1450713, orderType=1, beType=1`）：

```jsonc
{
  "items": [{
    "productCode": "9900004064", "quantity": 1,
    "roundList": [
      {"round": "1", "comboItemList": [{
         "code": "1406", "quantity": 1,
         "modification": {"values": [
           {"code":"102201","key":"0-0","quantity":0},   // 烤味酱：去掉 → A类传 unselectedKey，份数 0
           {"code":"120512","key":"0-1","quantity":1}    // 切块生菜：保留 → 传 selectedKey，份数 1
         ]}
      }]},
      {"round": "2", "comboItemList": [
         {"code":"4810","quantity":1}                    // 中薯条：supportModify=false，不传 modification
      ]},
      {"round": "3", "comboItemList": [{
         "code": "3050", "quantity": 1,
         "modification": {"values": [
           {"code":"200002","key":"1-1","quantity":1}    // 少冰 → B类，只传选中项
         ]}
      }]}
    ]
  }]
}
```

返回 `{"price": 3450, "originalPrice": 3450, "discount": 0}` → **34 元 5 角**。

### 6.2 `key` 与 `quantity` 的配合

| 项目状态 | key | quantity |
|---|---|---|
| 保留（默认选中） | `selectedKey` | 1 |
| 去掉（去酱/去生菜/去酸黄瓜） | `unselectedKey` | **0** |
| B 类单选（少冰/去冰） | 选中项的 `selectedKey` | 1 |

**`key` 决定状态，`quantity` 决定份数，两者都要给。**

### 6.3 换无糖可乐零差价 —— 已实证

把 round 3 的 `code` 从 `3050`（可乐中杯）换成 `3071`（无糖可口可乐中杯），其余完全不变：

```
code=3050  →  price 3450 分
code=3071  →  price 3450 分    ✅ 完全一样
```

`diffPrice: "+ ¥0"` 是真实的，不是显示问题。**控糖老人换无糖可放心作为默认动作。**

### 6.4 A 类调整不减价

去酱、去生菜实测**不影响价格**（3450 → 3450）。可以对老人说「不要钱」。

### 6.5 `calculate-price` 的价格单位是分（例外要注意）

| 字段 | 单位 |
|---|---|
| `price` / `originalPrice` / `discount` | **分** |
| `productPrice` / `productOriginalPrice` | 分 |
| `deliveryPrice` / `packingPrice` / `tablewarePrice` | 分 |
| `enjoyed.realDiscount` / `enjoyable.realDiscount` | **元**（唯一的例外） |

**展示前先 ÷100 再转「元/角」** —— 正好是 `scripts/a11y_format.py money` 的用途。

### 6.6 到店场景会返回 `takeWayList`（容易漏）

实测返回：

```json
"takeWayList": [
  {"code":"eat-in",     "title":"堂食", "subtitle":"店内用餐"},
  {"code":"locker-out", "title":"外带", "subtitle":"店外取餐柜"}
]
```

工具定义写明：「取餐方式 code，**到店下单时需要携带**」。

→ **模式 A 下单前必须让用户选堂食还是外带**，并把对应 `code` 传给 `create-order`。漏传会下单失败。

对应话术（一句话，不要解释「店外取餐柜」是什么）：

```
您在店里坐着吃，还是带走？
```

---

## 七、验收

改动后自查：

- [ ] 判断"能不能改"用的是 `choices[].supportModify`，不是顶层字段
- [ ] A 类组的所有项都传了（`selectedKey` 或 `unselectedKey`）
- [ ] B 类组只传了选中项的 `selectedKey`
- [ ] `diffPrice`（元字符串）与 `values[].price`（分）没有混淆
- [ ] 没有主动向用户展开完整 modification 列表
