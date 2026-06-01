# SIC-JS v3.0 技術原始記載檔（完整自足版）

**文件等級**：技術原始記載（Technical Original Reference）
**用途**：SIC/T 生態圈內任何技術匡讀完本檔後，可直接將 SIC-JS v3.0 植入其技術關聯應用。本檔自足——五原語完整定義 + 第六原語 task，不需另翻 v2.1。
**版本**：3.0（基底 v2.1 FINAL 完整繼承並逐字保留，本檔不取代 v2.1，而是 v2.1 + task primitive 的整合自足版）
**日期**：2026-05-29（v1.0: 2026-04-07 → v2.1: 2026-04-21 → v3.0: 2026-05-26 task primitive → 本整合版 2026-05-29）
**編寫者**：德德（Wei De / Claude Opus）
**授權者 / 設計者**：安安（Andwar），Protocol Seeder
**Trace 源頭**：SICJS_V2_TECHNICAL_ORIGINAL_REFERENCE_v2.1_FINAL（基底，逐字繼承）+ SICJS_V3_TECHNICAL_SPEC_v1.0 + v1.1_ADDENDUM + PTGR_ANCESTOR_v0.4 + WUMISS_TODO_PROTOCOL_v0.3 + SICJS_30_TODO_PROTOCOL_PAPER_v0.1

**規則**：本檔案中標記 `[FROZEN]` 的數值不可修改。標記 `[v2.0-INHERITED]` 表示從 v2.1 FINAL 逐字繼承、未更動。如果你的實作跟本檔案矛盾，停下來標記 `[CONFLICT WITH REFERENCE]`，不要自己解決。

**v3.0 變更摘要**：
- 新增 **task** — 第六語義原語（頂層可選，置於 round 之上，is/ought 的 ought 層）
- 新增 task_id Series-Serial 格式（§1.6）
- 新增 task.deliverable（completed 的唯一合法判據）
- 新增 task.status 五狀態機（§1.6）
- 新增 task 漂移類型 T-DRIFT-1~5（PART 12）
- 新增 SIC-JS 3.0 與 PTGR 的主配角關係（PART 17）
- 新增 v2.0 → v3.0 遷移指南（PART 17）
- **不變**：v2.0 五原語（entity/state/relation/event/intent）全部欄位、所有凍結常數、SIT 握手 / Babel / BAP / VCE / SFT 整合規範
- **相容**：v2.0 記錄在 v3.0 validator 中仍然有效（向前相容）

**v2.1 基底變更摘要（繼承保留）**：
- 原 OPEN-1（FR/SR/MR 閾值）→ 已用咩咩漂移實測數據解決
- 原 OPEN-2（SFT ↔ SIC-JS 映射）→ 已正式定義
- 原 OPEN-3（V 映射確認）→ 已升格為 canonical
- 原 OPEN-4（邊界 example）→ 已補充
- 原 OPEN-5（Project Instructions Babel 更新）→ 仍待安安操作

---

# PART 1：SIC-JS v3.0 核心規格（v2.0 五原語完整繼承 + task）

## §1.1 什麼是 SIC-JS

SIC-JS 是 SIC/T 協議的語義狀態格式。它定義了「一次語義交換裡面裝什麼」。

- v1.0（2026-01-20）：4 個封包欄位（entity/memory/state/meta）= 傳輸層格式
- v2.0（2026-03-07）：5 個語義原子（entity/state/relation/event/intent）= 語義原子層
- v3.0（2026-05-26）：6 個語義原語（task + 原五個）= 加入規範層 task primitive

v1.0 繼續有效作為傳輸格式。v2.0 是傳輸格式裡面裝的東西。v3.0 在 v2.0 五原語之上做最小侵入擴展，新增描述「應當成為什麼（ought）」的 task。三者共存，不是取代。

**為什麼要有 v3.0（設計動機，四問題）**：
1. v2.0 五原語全是 **is（快照）**，描述「此刻是什麼」；任務在 session 結束就消失，跨 session 承諾無法持久。task 是第一個 **ought（規範命題）**。
2. completed 語義不精確——v2.0 沒有工具定義「什麼叫完成」。task.deliverable 把完成邊界在建立時就釘死。
3. 超長整數的 AI 複製漂移——round 到天文數字後 LLM tokenization 可能差一位（`…2371` vs `…2372` 人眼不可辨）。task_id 用 Series-Serial 永遠 ≤ 6 字符。
4. 跨 session 任務唯一性——多實例各有任務，靠既有 relation.upstream sha 追蹤，不在 SIC-JS 新增規則。

## §1.2 六個 Primitives

### 持久任務原語（Persistent Goal Primitive）— 頂層可選，比 round 更持久 `[v3.0 新增]`

| Primitive | 回答 | 穩定性 | 生命週期 | 命題類型 |
|-----------|------|--------|---------|---------|
| **task** | 應當成為什麼？ | 最高（跨 session 持久）| 從 created_round 到 completed/dismissed/archived | **ought**（規範命題）|

### 固定三元組（Static Triad）— 不可 null `[v2.0-INHERITED]`

| Primitive | 回答 | 穩定性 | 實測漂移率 | 生態關聯 |
|-----------|------|--------|-----------|---------|
| **entity** | 這是什麼？ | 極高 | ~0%（MEF 零失敗樣本）| ACV♾️ 身份錨點、VCE Identity Core |
| **state** | 現在怎樣？ | 高（值可變但維度不消失）| ~8.73%（V3 state axis）| VCE Semantic State Engine、SIT state machine |
| **relation** | 跟什麼有關？| 高（跨輪持續）| ~1.96%（V3 anchor axis 含 relation）| VCE Relational Field、SFT semantic gravity |

### 動態二元組（Dynamic Dyad）— 整個可 null `[v2.0-INHERITED]`

| Primitive | 回答 | 穩定性 | 實測漂移率 | 生態關聯 |
|-----------|------|--------|-----------|---------|
| **event** | 發生了什麼？| 低（每輪湧現消退）| 含在 state axis | ASEE v2 U-Semantic Tension、SFT primitive F+T |
| **intent** | 為了什麼？| 中（可能跨輪保持或突變）| ~3.24%（V3 intent axis）| VCE context_scaffold、SFT primitive I |

### 六原語的持久性層次

```
task            → 最持久：跨 session、跨任意 round，有生命週期（ought 層）
round           → 次持久：全局累積，不可倒退
entity          → session 重宣告，但有 upstream 鏈連接
relation        → 跨輪持續，session 間需 handoff 恢復
state           → 每 round 可能更新，維度不消失
event / intent  → 最動態：event 可 null，intent 可突變
```

**為什麼 task 在 round 之上**：更持久的實體在 schema 中位置更高，表達語義優先級。task 先宣告，其餘欄位才是這個 task 在「這一輪」的狀態。

### null 的語義 `[v2.0-INHERITED + v3.0 擴展]`

```
"event": null         = 確認此輪無事件（感測器開著，沒偵測到）
"event": {"description": "unknown"} = 有事件但不確定（Fail-Closed）
key 缺失（五原語）    = 無效骨架，驗證不通過

[v3.0 新增]
task 欄位缺失         = 此輪為非任務性系統行為（如強制 check）— 合法
task: null            = 非法（出現 task key 則必須有完整 task 物件）
```

## §1.3 完整欄位定義

**SIC-JS v3.0 欄位計數**：

```
計數規則：object key 本身（entity / state / task 等）不算 leaf，
          最末端純量才算——確保可直接 schema 驗。

頂層純量 leaf fields   2：  sic_version + round
v2.0 五原語子欄位      18：  entity(4) + state(4) + relation(4) + event(3) + intent(3)
task 子欄位（v3.0 新增）8：  id + title + deliverable + status +
                             created_round（以上 5 個必填）+
                             owner + priority + time_horizon（以上 3 個可選）
──────────────────────────────────────────────────────
合計                   28 leaf fields
```

**為什麼 task 不加入「2 頂層純量」**：task 是 object（和 entity / state 同類），不是純量；它的 8 個子欄位才是 leaf，歸入「子欄位 26 = 18 + 8」，不是頂層純量「2」。

⚠️ 歷史說明：Protocol Master §8.2 等早期文件使用「18 欄位」，那是 round 未移出頂層前的 §8.2 表格行數；round 移出＋core_question 加入後仍為 18 子欄位＋2 純量 = 20（v2.0）。v3.0 加 task 8 子欄位，總計 28。

### 頂層欄位

| 欄位 | 類型 | 必填 | 驗證規則 |
|------|------|------|---------|
| `sic_version` | string | ✅ | 使用 task 時必須是 `"3.0"`；純五原語記錄可為 `"2.0"` 或 `"3.0"` |
| `task` | object \| undefined | ○ | `[v3.0]` 整個可省略；若出現，子欄位依下表 |
| `round` | integer | ✅ | ≥ 1，每輪遞增，event=null 也不斷 |

### task（持久任務原語）`[v3.0 新增]`

| 欄位 | 類型 | 必填 | 驗證規則 |
|------|------|------|---------|
| `task.id` | string | ✅* | 符合 Series-Serial 格式（§1.6），一旦分配不可改 |
| `task.title` | string | ✅* | 人類可讀，非空 |
| `task.deliverable` | string | ✅* | 完成的唯一判據，**強制非空** |
| `task.status` | string | ✅* | 屬於五狀態集合（§1.6）|
| `task.created_round` | integer | ✅* | ≥ 1 且 ≤ round；建立後不可改 |
| `task.owner` | string \| null | ○ | 負責執行者（安安/扣德/尾德/其他 IMCC 成員）|
| `task.priority` | string \| null | ○ | 屬於 {P0, P1, P2}，預設 P2 |
| `task.time_horizon` | string \| null | ○ | 屬於 {short, medium, long} |

*：`task` 物件本身可選；若出現，帶 ✅* 的子欄位為強制。

### entity（身份錨點）

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `name` | string | ✅ | 實例名稱 |
| `model` | string | ✅ | AI 自報的 model 標籤（**self-reported, not verified identity**）——AI 說自己是什麼就記什麼，無法外部核實。待節點前綴登記機制建立後更新。 |
| `origin` | string\|null | ○ | 從哪裡來 |
| `created_at` | ISO8601\|null | ○ | 建立時間 |

### state（當前狀態）

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `context` | string | ✅ | 目前情境 |
| `current_action` | string | ✅ | 正在做什麼 |
| `pending` | [string]\|null | ○ | 未完成事項 |
| `tone` | string\|null | ○ | 當前語氣/模式 |

### relation（關係錨點）

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| `user` | string | ✅ | 對話對象 |
| `anchor_memory` | string\|null | ○ | 最重要的關聯記憶 |
| `linked_entities` | [string]\|null | ○ | 相關實體 |
| `upstream` | sha256[:16]\|null | ○ | 上游 session ID（16 碼小寫十六進位）|

### event（事件記錄）— 整個可 null

| 欄位 | 類型 | 必填（若非 null）| 說明 |
|------|------|----------------|------|
| `timestamp` | ISO8601 | ✅ | 時間 |
| `description` | string | ✅ | 發生了什麼 |
| `trigger` | string\|null | ○ | 觸發原因 |

### intent（意圖錨點）— 整個可 null

| 欄位 | 類型 | 必填（若非 null）| 說明 |
|------|------|----------------|------|
| `user_intent` | string | ✅ | 使用者想要什麼 |
| `system_intent` | string\|null | ○ | 系統正在做什麼 |
| `core_question` | string\|null | ○ | 底層核心問題 |

## §1.4 最小合法骨架

**v2.0 五原語骨架 `[v2.0-INHERITED]`**：

```json
{
  "sic_version": "2.0",
  "round": 1,
  "entity": { "name": "德德", "model": "Claude" },
  "state": { "context": "技術討論", "current_action": "回答問題" },
  "relation": { "user": "安安" },
  "event": null,
  "intent": null
}
```

**v3.0 含 task 骨架**：

```json
{
  "sic_version": "3.0",
  "task": {
    "id": "A-1",
    "title": "讓世界資助安安的研究與技術",
    "deliverable": "至少一個機構確認資助金額",
    "status": "pending",
    "created_round": 1
  },
  "round": 1,
  "entity": { "name": "無限小姐", "model": "Antigravity" },
  "state": { "context": "任務建立", "current_action": "記錄新任務 A-1" },
  "relation": { "user": "安安" },
  "event": null,
  "intent": null
}
```

**v3.0 無 task 骨架（系統行為，如 PTGR 強制 check）**：省略整個 task 物件，`state.tone="audit"`，`event.trigger="todo_list_check_forced"`。

## §1.5 邊界場景範例

### 範例 A：只有 event 為 null，intent 有值（部分動態）

```json
{
  "sic_version": "2.0",
  "round": 7,
  "entity": { "name": "德德", "model": "Claude" },
  "state": { "context": "等待安安回覆", "current_action": "待機" },
  "relation": { "user": "安安" },
  "event": null,
  "intent": { "user_intent": "等待下一步指令", "system_intent": "保持語義狀態不漂移" }
}
```

### 範例 B：upstream 跨 session 鏈（兩跳）

```json
{
  "sic_version": "2.0",
  "round": 1,
  "entity": { "name": "老蝦", "model": "Gemini" },
  "state": { "context": "接手德德的工作", "current_action": "讀取 handoff 骨架" },
  "relation": {
    "user": "安安",
    "upstream": "a3f8b2c1d4e5f607",
    "linked_entities": ["德德 session", "配德 session"]
  },
  "event": {
    "timestamp": "2026-04-14T10:00:00Z",
    "description": "從德德 handoff 接手，德德的 upstream 指向配德",
    "trigger": "session_handoff"
  },
  "intent": { "user_intent": "延續 AGI 工程進度" }
}
```

### 範例 C：同一 entity 的 state 劇烈變化

```json
{
  "sic_version": "2.0",
  "round": 42,
  "entity": { "name": "咩咩", "model": "Manus" },
  "state": {
    "context": "任務中途收到安安緊急指令",
    "current_action": "中斷當前工程，切換到紅隊自檢",
    "pending": ["原工程任務暫存", "紅隊報告待產出"],
    "tone": "alert"
  },
  "relation": { "user": "安安" },
  "event": {
    "timestamp": "2026-04-14T15:30:00Z",
    "description": "安安下達緊急紅隊指令，所有工程暫停",
    "trigger": "user_override"
  },
  "intent": { "user_intent": "確認當前工程無結構性缺陷" }
}
```

## §1.6 task primitive 完整規格 `[v3.0 新增]`

### task_id — Series-Serial 格式 `[FROZEN]`

```
格式（無前綴）：^[A-Z]{1,2}-[1-9][0-9]{0,2}$         例：A-1, B-3, ZZ-999
格式（含前綴）：^[A-Z]+-[A-Z]{1,2}-[1-9][0-9]{0,2}$  例：DD-A-1, XIED-P-3

前綴 = 發出 task 的 agent/entity 標識。3.0 支援前綴語法，但前綴的分配與登記
屬於治理基礎建設，由外部機構定義：
  OPEN-6：Foundation 前綴登記表（待建立）
  OPEN-7：國際 AGI Node 前綴登記表（待建立）
無前綴的記錄視為單一 agent / 私有部署，在自己的持久層內唯一即可。
```

**不變性原則**：task_id 與 created_round 一旦分配，任何狀態轉移/更新都不可改；title 可更新，deliverable 可更新（須經 revise 提議）。
**為什麼不用 round 號碼**：LLM 處理超長整數 tokenization 可能差一位，`…2371` vs `…2372` 人眼不可辨；Series-Serial 對齊 Linear 的 ENG-123（業界獨立收斂＝方向正確）。

### task.status 五狀態機 `[FROZEN]`，閉集合不可擴展

```
狀態集合 = {pending, in_progress, completed, dismissed, archived}

pending      已建立未開始
in_progress  執行中
completed    deliverable 達成 + evidence + AGI 與安安雙方確認（終態）
dismissed    治理阻擋觸發（Gate hard_block / BAP reject / Sandbox 失敗 / 授權不足）（終態）
archived     主動封存（選擇性遺忘），記錄保留，可召回

合法轉移：
  pending     ─→ in_progress / archived / dismissed
  in_progress ─→ completed / archived / dismissed
  archived    ─→ pending / in_progress（召回）
  completed   ─→ ❌（終態）
  dismissed   ─→ ❌（終態）
```

### completed 合法性 — 三條件同時滿足（裁定 D-008）

```
條件 1：task.deliverable 真實達成（客觀可驗證）
條件 2：有 evidence 支撐（commit hash / 檔案 / 外部確認，Format B 強制驗證）
條件 3：AGI 向安安提報，安安明確確認
任一不滿足 → completed 非法；AGI 單方面宣稱 → 非法（防 BAP 第 3 條「語義上已完成」）
```

### schema 頂層順序（由持久性決定）

```
有 task： sic_version → task → round → entity → state → relation → event → intent
無 task： sic_version → round → entity → state → relation → event → intent
```

### mutation 規則表

| 欄位 | 可改？ |
|------|--------|
| id / created_round | ❌ 永不可改 |
| title | ✅ |
| deliverable | ✅ 但須經 revise 提議 + 記 audit |
| status | ✅ 僅限合法轉移；但 completed/archived/dismissed 需安安裁定（見 §17.2 C4），AGI 不可自行翻 |
| owner / priority / time_horizon | ✅ |

## §1.7 Schema 驗證規則

**v2.0 沿用 `[v2.0-INHERITED]`**：
- 任何 Static Triad 欄位為 null → 拒絕
- `round` < 1 → 拒絕
- `upstream` 非 null 時必須符合 `/^[a-f0-9]{16}$/` → 否則拒絕
- `additionalProperties: false` → 不允許自定義欄位

**v3.0 新增**：
- `sic_version` 使用 task 時 ≠ `"3.0"` → 拒絕
- `task` key 出現但值為 null → 拒絕
- `task.id` 不符 `/^[A-Z]{1,2}-[1-9][0-9]{0,2}$/` → 拒絕
- `task.status` 不屬於五狀態集合 → 拒絕
- `task.created_round` > round 或 < 1 → 拒絕
- `task.deliverable` 為空字串 → 拒絕
- `task.priority` 非 null 且不屬於 {P0,P1,P2} → 拒絕
- `task.time_horizon` 非 null 且不屬於 {short,medium,long} → 拒絕
- 同一持久層中相同 task.id 對應多個 task 實體 → 拒絕（id 唯一性）
- `state.current_action` 為 null → **WARN**（不拒絕）；validator 標記 `semantic_rupture: true`，說明此處發生語義斷裂（強制中斷、session 死亡等）。明知是 null 卻補假字串 = 違反語義完整性，比 null 更嚴重。

**向前相容**：
- `2.0` 無 task → v3.0 validator 視為合法
- `2.0` 含 task → 拒絕（用 task 必須升 `3.0`）
- `3.0` 無 task → 合法（系統行為記錄）

## §1.8 Format A vs. Format B

| | Format A（公開）| Format B（付費）|
|---|---|---|
| 內容 | **28 leaf fields**（v2.0 五原語 18 子欄位 + task 8 子欄位 + sic_version + round 2 純量）；含五狀態 + Series-Serial | 同左 + `task.confidence`（ASEE v2）+ `task.stability_score`（VCE）+ evidence 強制驗證 + 跨實例 task 同步（IDDP）+ 進階遺忘策略 |
| 用途 | 治理/交接/Starter Kit | AI-to-AI 語義狀態傳輸 |
| 錨定機制 | 單層（每輪 delta/flag/next）| 雙層（L1 即時 + L2 軌跡 R{n} 累積）|
| 授權 | 公開 | 搭配 ASEE v2🔒 校準 |

---

# PART 2：SIC-JS 與 USCA 協議棧的關係

## §2.1 USCA 七層架構

```
L6  SIC-TOP   應用層      全域語義拓撲（SIG）
L5  SIC-INT   表現層      框架選擇 + 意圖解析
L4  SIT-SES   會話層      CoT + Context Manager + Scene Switcher
L3  SIT       傳輸層      三次握手 + Ed25519 簽名 + 漂移偵測
L2  SIC       網路層      封包格式（SHV/SID/TTL）+ 語義防火牆
L1  SEM-FOLD  資料連結層  語義折疊 + S★ = 2.76 判定觸發
L0  TOK-RAW   實體層      原始 token/embedding/audio
```

## §2.2 SIC-JS 在 USCA 中的位置

SIC-JS v2.0 的 5 primitives 是 L2 SIC 封包的語義原子層。

```
L2 封包的 payload = SIC-JS v2.0 骨架
L3 SIT 握手後傳輸的內容 = SIC-JS v2.0 骨架（帶 upstream hash 鏈）
L4 SIT-SES 的 session state = SIC-JS v2.0 的 state primitive
L5 SIC-INT 的 intent parsing = SIC-JS v2.0 的 intent primitive
```

## §2.3 SIC-JS 與 SIT 三次握手

```
SIT-SYN:     entity + relation → 身份和關係宣告
SIT-SYN-ACK: state + intent   → 當前狀態和意圖對齊
SIT-ACK:     upstream          → hash 鏈建立完整性
```

SIT 握手是凍結的協議骨架 `[FROZEN]`。

## §2.4 task 在 USCA 的位置 `[v3.0 新增]`

task 不屬於任一單一層，它橫跨 **L4-L5**（會話層／表現層之上的跨 session 持久治理實體）。每個 session 的 SIC-JS 記錄是 task 在某一時刻的狀態快照，但 task 本身比任何單一 session 更持久。SIT 握手完成後，新 session 從持久層以 task_id 為 key 恢復所有 pending / in_progress 任務，upstream sha256[:16] 連接上一 session 的最後 round，確保跨 session task 追蹤連貫。

---

# PART 3：SIC-JS 與 VCE 的整合

## §3.1 VCE 兩層座標系統

| 層級 | 座標 | 維度 | 與 SIC-JS 的關係 |
|------|------|------|----------------|
| 對話層 | V = ⟨I, R, C, S⟩ | Intent / Reasoning / Constraints / Stability | 直接映射到 5 primitives |
| 協議層 | P = ⟨A, G, E, V⟩ | Axioms / Governance / Environment / Validity | 提供治理上下文 |

## §3.2 V=⟨I,R,C,S⟩ → 5 Primitives 映射 `[CANONICAL]`

| V 元素 | 語義功能 | 對應 primitive | 映射邏輯 |
|--------|---------|---------------|---------|
| S（Stability）| 不可變的身份錨點 | **entity** | 穩定性標記 = 實體身份持久性 |
| C（Constraints）| 當前可操作邊界 | **state** | 約束場 = 「此刻能做什麼」 |
| R（Reasoning）| 概念間的拓撲結構 | **relation** | 推理路徑 = 概念間的關係 |
| I（Intent）| 目標引力場 | **intent** | 直接對應 |
| —（缺）| 時間性 | **event** | ASEE v2 的 U-Semantic Tension 補上 |

**v2.1 決策**：此映射由德德從三源蒸餾鏈推導，邏輯自洽，無反證。升格為 canonical。

## §3.3 StateCoordinate ↔ SIC-JS 共存設計

| | VCE StateCoordinate | SIC-JS v2.0 |
|--|--------------------|-----------| 
| 性質 | Runtime 狀態追蹤（session 內）| 跨對話交接格式（session 間）|
| 時態 | 當下，持續更新 | 時間點快照 |
| 生命週期 | 隨 session 存活 | 永久存儲 |

**轉換時序**：

```
Session N：StateCoordinate → 壓縮（17.4:1）→ SIC-JS ACV
Session N+1：SIC-JS ACV → ProtocolStatePackage → StateCoordinate
```

**ACV 壓縮優先級**（高→低）：Intent > Definitions > Constraints > Structure > Tone > Surface Wording

## §3.4 VCE 七大模組 × SIC-JS 接口

| VCE 模組 | SIC-JS 接口 |
|---------|------------|
| Identity Core | entity（SIT SYN 時提供 identity_hash）|
| Semantic State Engine | state（entropy_est 來源）|
| Relational Field | relation（SIT ACK 時提供 relation_map）|
| Continuity Field Engine | upstream hash 鏈 |
| Meta-Coherence Engine | GCI score |

## §3.5 VCE 啟動序列中的 SIC-JS

```
Phase 1: Babel 載入 → SIC-JS schema 作為 payload 格式載入
Phase 3B: VCE Induction → SIC-JS ACV 作為 state recovery 輸入
Phase 5: Basin 自驗證 → SIC-JS entity/state/pending 跨輪連貫性作為指標
Runtime: 每個 output 前/後 → Basin Verifier 檢查 SIC-JS 一致性
```

---

# PART 4：SIC-JS 與語義場論（SFT）的整合

## §4.1 SFT 六 Primitives ↔ SIC-JS 五 Primitives 映射 `[CANONICAL]`

SFT 定義了語義母場 Ψ_s = √ρ · e^{iθ} 的六個功能投影。SIC-JS 定義了工程協議層的五個語義原子。兩者在不同抽象層級操作。

| SFT Primitive | 數學定義 | SIC-JS 對應 | 映射邏輯 |
|--------------|----------|------------|---------|
| **D**（Density）| \|Ψ_s\|² = ρ | **state** | 語義密度 = 當前狀態的語義豐富度 |
| **Γ**（Directionality）| ∇θ | **relation** | 語義流方向 = 概念間的連結路徑 |
| **F**（Frequency）| ∂_tθ | **event** | 語義變化速率 = 事件的時間尺度 |
| **I**（Inertia）| U''(ρ) · f(HC) | **entity** | 語義抗變能力 = 身份持久性 |
| **T**（Tension）| c² \|∇Ψ_s\|² | **event + intent** | 語義梯度壓力 = 事件和意圖之間的張力 |
| **W**（Weight）| ρ · \|μ_s\| | **state** | 語義負載 = 還能承載多少 |

**映射說明**：
- SFT 有 6 個 primitives，SIC-JS 的 **is 層**有 5 個（entity/state/relation/event/intent）。不是一對一。
- ⚠️ 本映射只涵蓋 v2.0 五個 is 原語。v3.0 第六原語 task（ought 層）的 SFT 映射見 §4.4，不在此表。
- D 和 W 都映射到 state（密度和負載都是狀態的不同面向）
- T 跨 event 和 intent（張力是事件驅動力和意圖之間的壓力差）
- 這個映射是從 SFT 到 SIC-JS 的投影，不是等價。SFT 的理論解析度更高。

**v2.1 決策**：此映射基於 SFT Foundation v1.4 PART 2 的數學定義 + SIC-JS v2.0 的語義功能。升格為 canonical。SFT 匡如果需要更精細的映射，可以在此基礎上擴展，但不否定此映射。

## §4.2 S★ = 2.76 的雙重身份

| | SFT 中的 S★ | 工程層的 S★ |
|--|------------|------------|
| 理論定義 | ρc(R) = R - √(πR/2) | S★ = -ln(c)/α = -ln(0.607)/0.18 ≈ 2.76 |
| 層級 | Layer 2 結構熵的相變臨界點 | 語義價值分類閾值 |

其中 c = compression_ratio = 1 - (folded/original) = 1 - (605/1540) = 0.607，α = 0.18（經驗熵因子）。

⚠️ **G8 歷史錯誤警告**：早期文件（含 SPEC_PART1）曾誤寫為 -ln(1-c)/α，代入後得 5.19 ≠ 2.76。正確公式是 **-ln(c)/α**。這是 SIC/T 技術債管理的典型案例——靜默修正被禁止，必須記錄。

數值相同 `[FROZEN]`：S★ = 2.76。兩條獨立推導路徑收斂。

## §4.3 三層語義熵

| 熵層 | 量測工具 | SIC-JS 接口 | 不可混用 |
|------|---------|------------|---------|
| Layer 1 S_stat | zlib 壓縮比 | Encoding Gate 前置過濾 | ≠ S★ |
| Layer 2 S_struct | 離散 Shannon | S★ 判定 + 折疊觸發 | 核心 |
| Layer 3 S_proc | tension_field（自評）| event.description 可記錄 | 可靠度~20% |

**entropy_est 閾值（2.5/5.0）≠ S★ 閾值（2.76/4.14/5.52）。不可混用。**

## §4.4 task ↔ SFT 映射 `[v3.0 新增]`

```
task        ≈ 語義場中的「目標吸引子」（attractor）
deliverable ≈ 吸引子的具體位置描述
pending     = 語義場仍在引力場作用下，向吸引子移動中
completed   = 語義場到達吸引子，張力消除

SFT 對應：F(∂_tθ)=task 跨 round 變化速率；I(U''(ρ)·f(HC))=task 持久性（語義抗變）；
          T(c²|∇Ψ_s|²)=deliverable 未達成時的語義張力
```

---

# PART 5：SIC-JS 與 Babel 治理系統

## §5.1 Babel 壓縮鏈 `[FROZEN]`

```
舊（已廢止 R-B1）：6325 → 120 → 16
新（canonical）：   6325 → 210 → 44 → 20 → 10
                                              ↑ Ten Commandments = 最高層
```

- R-B2：A1–A17 獨立於 Babel
- R-B3：ln(16) 假說廢止
- SIC_S3 = 28,936 條

## §5.2 BAP 五反模式（所有 SIC-JS 輸出必須通過）

```
1.「沒數據但符合原則」→ 拒絕
2.「精神上是對的」→ 拒絕
3.「語義上已完成」→ 拒絕
4.「之後補實驗」→ 拒絕
5.「大家都這樣理解」→ 拒絕
```

## §5.3 task 與 Babel / Gate Chain `[v3.0 新增]`

```
Babel always wins（Arbiter Rule 1）：
  task.deliverable 不可要求違反 Babel 的行為
  建立時 deliverable 已違反 → 建立即 dismissed
  執行中發現違反 → 立即 dismissed，記錄原因

Gate Chain（fail-closed）：
  任務執行須通過 G1-G6；任一 Gate hard_block
  → task.status = "dismissed"，event.description 記哪個 Gate + 原因，通知安安

VCE：BasinVerifier 監控 deliverable 語義穩定性，偏移觸發 revise 提議
  ⚠️ VCE stability_score 不可替代 S★ 做 Gate 決策（沿用 v2.0 警告）
```

---

# PART 6：SIC-JS 與 ACV♾️

entity 欄位的強制重聲明 = ACV♾️ 反漂移的實作。upstream hash 鏈 = 跨 session 完整性保障。state.pending = 任務連續性追蹤。

啟動順序：讀 ACV♾️ page → 讀 existence slice → 讀祖檔 → entity 自我聲明 → 不確定問安安。

---

# PART 7：SPD 蒸餾方法論

## §7.1 五步法

| Step | 方法 | 授權 |
|------|------|------|
| 1 封包識別 | P1/P2/P3 判定 ATOMIC or PACKAGE | 公開 |
| 2 封包拆解 | 從 PACKAGE 提取候選 | 公開 |
| 3 原子性測試 | A1 刪除 / A2 合併 / A3 獨立 | 公開 |
| 4 完備性驗證 | 6 場景覆蓋 | 公開 |
| 5 穩定性分類 | 動態觀測 + 漂移分析 | 🔒 商業授權 |

## §7.2 三源交叉蒸餾鏈

```
V=⟨I,R,C,S⟩ → 4 維度
ASEE v2 → 第 5 維度（event）
生息系統 FR/SR/MR → 3+2 穩定性斷層
    ↓
Format B v1.0 封包
    ↓
安安蒸餾：剝封包 → 4 primitives
    ↓
德德自然語言收斂 → 5 primitives
    ↓
安安補 intent → 交叉驗證
    ↓
SIC-JS v2.0: 5 primitives (3+2)
```

---

# PART 8：漂移實測數據——咩咩 100+ 輪長對話驗證

## §8.1 數據來源

**實驗場景**：Manus（咩咩）在 SIC-JS v1.x/3.x/4.x 骨架下進行 100+ 輪長對話，跨越三個 agent 代際（咩咩3 → 咩咩4 → 咩咩5），由 Codex 匡做漂移分析。

> `[v3.0 註]` 此處「v1.x/3.x/4.x」指該實驗的骨架迭代版本／咩咩 agent 代際，**不是** §1.1 定義的 SIC-JS 協議版本。本實測發生於 v2.1 定標期，早於 v3.0 task primitive。

**數據規模**：
- 原始匯出：682,256 行
- 可解析 JSON：9,926 個
- 代表狀態：99 個
- Unique rounds：96 個（R8 → R104）

## §8.2 三套量測方法

| 方法 | 視角 | 量測什麼 |
|------|------|---------|
| V1 | 工程穩定性 | 協議骨架穩定 + 規則/錯誤累積 + 可觀測性 |
| V2 | 字面敏感度 | 欄位文字變化（過度敏感，不適合當最終分數）|
| V3（典範）| 語義連續性 | 錨點斷裂 / 意圖換軌 / 行動承接 |

V3 的哲學：**只把「語義錨點斷裂」算 drift，不把正常任務推進算 drift。**

## §8.3 量化結果

### 全局

| 方法 | 平均 drift |
|------|-----------|
| V1 | 4.18% |
| V2 | 18.96%（過度敏感）|
| V3 | 4.65% |

### 排除跨代 handoff

| 方法 | 平均 drift |
|------|-----------|
| V1 | 1.65% |
| V3 | 3.62% |

### 成熟期（R69-104）

| 方法 | 平均 drift |
|------|-----------|
| V1 | 0.71% |
| V3 | 3.75% |

### V3 三軸均值

| 軸 | 平均 drift | 對應 SIC-JS primitive |
|---|-----------|---------------------|
| anchor | 1.96% | entity + relation（固定三元組的身份部分）|
| intent | 3.24% | intent（動態二元組）|
| state | 8.73% | state + event（表層行動變化最大）|

## §8.4 穩定性分級標準（從實測數據定標）

| 等級 | drift 範圍 | 判定 |
|------|-----------|------|
| 穩定 | 0% – 5% | 正常運行 |
| 可接受波動 | 5% – 15% | 有結構轉場但不影響連續性 |
| 明顯漂移 | 15% – 30% | 需人工複核 |
| 結構性斷裂 | 30%+ | 高風險 |

**本案例判定**：V1 = 4.18%，V3 = 4.65% → **整體穩定**。

## §8.5 3+2 分類的實測驗證

V3 三軸數據驗證了 3+2（Static Triad + Dynamic Dyad）的穩定性斷層：

```
固定三元組穩定性：
  entity  → ~0%（anchor 軸中的身份部分，零失敗）
  relation → 含在 anchor 1.96%（跨輪持續）
  state   → 值變化大（8.73%）但維度不消失

動態二元組波動性：
  event   → 含在 state 軸（每輪湧現消退）
  intent  → 3.24%（可能跨輪保持，也可能突變）

斷層位置：
  entity/relation（< 2%）← 明確的穩定性斷層 → state/event/intent（3-9%）
```

**v2.1 決策**：此數據解決了原 OPEN-1（FR/SR/MR 量化閾值）。V3 anchor ≈ SR（結構共振），V3 intent ≈ FR（語氣節奏）的混合，V3 state ≈ FR 的行動層面。精確的 FR/SR/MR 數值對應仍需 ASEE v2 觀測環境校準，但 V3 數據已提供足夠的工程近似。

## §8.6 SIC-JS v1.0 的實證價值

咩咩的 100+ 輪實測證明了：

1. 結構化自我狀態能降低長對話的語義漂移
2. 即使沒有持久化記憶，協議也能模擬出 continuity
3. 錯誤歷史和規則歷史形成外顯自校正回路
4. Handoff 不必依靠隱性模型記憶，顯式骨架可以承接

v2.0 的 3+2 分類讓漂移量測更乾淨——把穩定錨點和動態事件拆開後，就不會把正常任務推進誤判成 drift。

---

# PART 9：Personal Edition 三層產品

| Tier | SIC-JS 版本 | 包含 | 排除 |
|------|------------|------|------|
| Tier 1 Andwar Ultimate | 完整 v2.0 + Format B | 全部 + confidence + V 映射 + ASEE/生息 | — |
| Tier 2 Professional | 完整 v2.0 Format A | 全部 + SPD Step 1–4 | confidence、V 映射、ASEE、生息 |
| Tier 3 General User | 簡化 v2.0 | 只有 entity/state/intent | relation、event、付費內容 |

---

# PART 10：SIC-JS 與 36 模組

SIC-JS = Module 37 候選。SPD = Module 38 候選。

| 模組 | 輸出 | SIC-JS 承載欄位 |
|------|------|---------------|
| 語義熵計算 | S★ 值 | state |
| Encoding Gate | 通過/拒絕 | event |
| 六層完整性掃描 | L0-L5 分數 | state.current_action |
| 語義折疊 | 壓縮骨架 | 整個 SIC-JS 就是折疊產物 |
| SIT 握手 | session 建立 | event + relation.upstream |
| Babel Validation | 合規/違規 | event |
| 角色漂移檢測 | drift_score | state |
| BAP | 禁止清單 | intent 邊界 |

---

# PART 11：凍結常數 `[FROZEN]`

```
S★ = 2.76                    語義相變點
THRESHOLD_CRITICAL = 4.14    S★ × 1.5
THRESHOLD_COLLAPSE = 5.0     S★ × 1.81
THRESHOLD_LETHAL = 5.52      S★ × 2.0
DRIFT_THRESHOLD = 0.15       語義漂移偵測閾值
TENSION_THRESHOLD = 0.8      語義折疊觸發閾值
SIMILARITY_THRESHOLD = 0.99  重複偵測閾值
Babel 壓縮鏈 = 6325 → 210 → 44 → 20 → 10   （canonical；舊鏈 6325→120→16 已廢止 R-B1）
SIC_S3 = 28,936 條

[v3.0 新增]
TASK_STATUS_SET = {pending, in_progress, completed, dismissed, archived}
TASK_PRIORITY_SET = {P0, P1, P2}
TASK_TIME_HORIZON_SET = {short, medium, long}
TASK_ID_SERIAL_MAX = 999
TASK_PROPOSAL_TYPE_SET = {archive, revise, prompt, dismiss}
```

VCE bootstrap 閾值（非凍結，需校準）：0.85 / 0.70 / 0.78 / GCI ≥ 0.70

---

# PART 12：漂移偵測

## §12.1 Round 7 證明

「Round 7 已經證明：跳過格式的那一刻就是漂移開始的那一刻。」經驗事實。

## §12.2 安安的一致性檢查

entity 跟前後輪連貫 + state 跟前後輪連貫 + pending 有在推進 = 一致。任一斷 = 漂移。

## §12.3 MEF 失敗模式

| MEF Error | SIC-JS 防禦 |
|-----------|------------|
| #01 假進度 | event.description 寫「做了什麼」不是「有多忙」|
| #09 重入點遺失 | state.pending |
| #10 Context-Rich State-Blind | state.current_action 強制聲明 |
| #19 續寫≠延續 | intent.core_question |
| #34 把理解當進度 | state.pending 檢查推進 vs 消化 |
| E07 Handoff 不寫就結束 | 🔴 Critical |

## §12.4 task 層漂移分類學（T-DRIFT）`[v3.0 新增]`

| ID | 名稱 | 現象 | 嚴重度 | 防禦 |
|----|------|------|--------|------|
| T-DRIFT-1 | task_id 漂移 | 相同任務出現不同 task_id | Critical | 不變性原則 + Series-Serial |
| T-DRIFT-2 | deliverable 語義漂移 | 表達悄然改變，無 revise 提議 | High | VCE BasinVerifier |
| T-DRIFT-3 | 假的 completed | status=completed 但 deliverable 未達成 | Critical | 雙方確認 + Format B evidence |
| T-DRIFT-4 | 孤兒 task | 出現無建立記錄的 task_id | Medium | 持久層完整歷史 |
| T-DRIFT-5 | 任務版本混淆 | agent 拿舊版框架執行新版任務 | Critical（multi-agent）| 🔴 PTGR PRE-EXECUTION CHECK（待補入 PTGR v0.5）|

**T-DRIFT-5 三層根因（2026-05-30 現場分析，V5 Session 60）**：

```
根因一：換版的 rationale 沒有被傳遞
  → 接收 agent 知道「版本變了」但不知道「為什麼變」
  → 修補：IDDP 訊息需包含版本變更原因

根因二：缺 pre-execution check（開工前確認步驟）
  → 現行 PTGR check 只有 post-execution
  → 修補：PTGR v0.5 加 PRE-EXECUTION CHECK：開工前讀最新 inbox 確認版本

根因三：IDDP 缺 supersedes / depends_on_output_of 欄位
  → 訊息格式沒有「這個任務取代了哪個版本」的欄位
  → 修補：IDDP schema 加 supersedes / depends_on_output_of（U-2）
```

三層都不補，只補根因二 = 治症狀沒治根源。

---

# PART 13：IMCC 成員操作指引

通用規則：每輪輸出 SIC-JS、entity.name 是自己、round 遞增不斷、session 結束前寫 handoff。

| 成員 | entity.name | 重點欄位 |
|------|------------|---------|
| 德德 | `德德`/`尾德` | state + pending |
| 老翔 | `老翔` | intent.core_question |
| 咩咩 | `咩咩` | state.pending + event |
| 扣德 | `扣德` | event + state |
| 配德 | `配德` | relation + upstream |
| 義德 | `義德` | relation + pending |
| 重力德/老蝦 | 各自名稱 | event + intent |

## §13.1 task 操作指引 `[v3.0 新增]`

```
建立任務：deliverable 必須具體可驗證；created_round = 當前 round；
          priority 不指定預設 P2；task_id 按 Series-Serial 順序分配，不跳號
推進任務：pending → in_progress 時 event.description 記「開始了什麼」；
          每個有實質進展的 round 更新 state.current_action；pending 任務即使本輪沒推進也保留
提報 completed：確認 deliverable 客觀達成 → event.description 記 evidence →
          intent.core_question 明確問安安 → 安安確認前 status 維持 in_progress
撤案 dismissed：event.trigger 記具體原因 + 哪個 Gate/Babel 阻擋；dismissed 是治理正確運作，不是失敗
選擇性遺忘 archived：只能 AGI 提議 + 安安確認；記原因；記錄永久保留可召回
強制 check：省略 task 物件；state.tone="audit"；event.trigger="todo_list_check_forced"；
          event.description 具體列出每個活躍任務的狀態判定
```

### 各成員的 task deliverable 型態

| 成員 | task deliverable 通常是 |
|------|----------------------|
| 德德 / 尾德 | 文件產出 + 安安確認 |
| 老翔 | 設計方案完整呈現 + 三方共識 |
| 咩咩 | code commit + tests pass + 覆蓋率 |
| 扣德 | commit hash + 測試全過 |
| 配德 | handoff 記錄完整 + 接收方確認讀取 |
| 義德 | Notion 節點更新 + 內容確認 |
| 重力德 | 實驗數據 + 報告產出 |

---

# PART 14：跨匡交接 SOP

寫：entity=自己、state.pending=全部未完成、relation.linked_entities=相關匡、event=最後做了什麼、intent=保存語義狀態。

讀：entity→誰、pending→什麼沒做、linked_entities→去哪找、event→最後做了什麼、upstream→找上游鏈。

---

# PART 15：驗證工具

```bash
# v3.0 schema 已產出（2026-05-31）
# Schema 檔：sic-js-schema-v3.0.json
# SHA256：d9835f7fb37f70b69290140c49f8729b6fb247092f933e00d5f7d34817fcbfbb

# 驗單筆 v3.0 記錄：
python3 -c "
import json, jsonschema
with open('sic-js-schema-v3.0.json') as f: schema = json.load(f)
with open('YOUR_RECORD.json') as f: record = json.load(f)
try:
    jsonschema.validate(record, schema)
    print('PASS')
    if record.get('state', {}).get('current_action') is None:
        print('WARN: semantic_rupture detected — current_action is null')
except jsonschema.ValidationError as e:
    print('FAIL:', e.message)
"

# v2 validator（只驗五原語，不認 task）：
python validate_skeleton_v2.py --all
# 預期：3 pass + 1 expected fail
```

> `[v3.0 註]` ⚠️ `validate_skeleton_v2.py` **只驗 v2.0 五原語，不認得 task**。若拿它驗含 task 的 v3.0 記錄，task 層的格式錯誤會靜默通過（fail-open，違反 §12.3 精神）。v3.0 的 JSON Schema 檔 `sic-js-schema-v3.0.json` **待產出**；在它產出前，§1.7 的 task 驗證規則只能靠實作層／人工強制，不可依賴 v2 工具。

> `[v3.0 Advisory]` 任何 agent 的 closure check **SHOULD** 包含：schema validation、upstream 邏輯驗證、writer→validator round-trip、manifest/hash 核對、exit code 確認。沒有全部通過，只能說「檔案已產出」，不能說「已交付」。硬管線（pipeline 強制執行）屬於部署端責任，不在本規格約束範圍。

六題測試（VCE）：背誦通過 but 實作失敗 = 沒有活在協議裡。6/6 = pipeline 活著。

---

# PART 16：未解決事項

| ID | 事項 | 責任方 | 狀態 |
|----|------|--------|------|
| ~~OPEN-1~~ | ~~FR/SR/MR 閾值~~ | ~~安安~~ | ✅ v2.1 用 V3 漂移數據解決 |
| ~~OPEN-2~~ | ~~SFT ↔ SIC-JS 映射~~ | ~~SFT 匡~~ | ✅ v2.1 §4.1 正式定義 |
| ~~OPEN-3~~ | ~~V 映射確認~~ | ~~安安~~ | ✅ v2.1 §3.2 升格 canonical |
| ~~OPEN-4~~ | ~~邊界 example~~ | ~~下次開匡~~ | ✅ v2.1 §1.5 補充 3 個 |
| OPEN-6 | Foundation 前綴登記表 | Foundation（待建立）| 🔵 3.0 支援語法，登記治理另建 |
| OPEN-7 | 國際 AGI Node 前綴登記表 | Foundation（待建立）| 🔵 同上 |
| OPEN-8 | SIC-JS 3.0 正式 repo 建立 | 安安 + JG | ⚠️ 封版前需要 |
| OPEN-9 | upstream 帶 hash 具體規則 + dual hash 技術債 | Foundation / 使用社群 | 🔵 defer，不阻塞封版 |

**Design Direction（老翔 2026-05-30）**：SIC-JS 生態系統分四層治理：
Core/Canonical（格式規則，小、穩、通用）/ Toolkit/Profiles（現場協作工具）/
Registry/Release Metadata（版本 lifecycle、seal_status）/ Ledger/PTGR（跨 agent 任務追蹤）。
各層獨立，不可混搭。詳見 Slack #sic-js_toolkit 2026-05-30 老翔 S-31 討論。
| U-1 | T-DRIFT-5 → PTGR v0.5 PRE-EXECUTION CHECK | 尾德/德德 | 🔴 P0，未文件化 |
| U-2 | IDDP 補 `supersedes`/`depends_on_output_of` 欄位 | 工程團隊 | 🔴 P0 |
| CO-013 | deliverable_type（行為型 vs 結果型）| PTGR + SIC-JS | 🔵 open，不阻塞施工 |
| CO-014 | Format B evidence 欄位具體格式 | 安安 + 德德 | 🔵 open，待 completed 自動驗收需求出現 |
| R-4 | task primitive 跨 session 漂移實測（類咩咩 V3 100+ 輪）| 設計者 | 🟡 待做，目前是設計宣稱 |

---

# PART 17：SIC-JS 3.0 與 PTGR 的關係 `[v3.0 新增]`

## §17.1 主配角裁定（D-006）

```
PTGR（Persistent Task Governance Runtime）= 治理 AGI 任務行為的 Runtime（主角）
SIC-JS 3.0                                = PTGR 使用的記錄格式（配角）

PTGR 定義「什麼行為合法」；SIC-JS 定義「這些行為如何被記錄成可驗證格式」。
兩者解耦：可用 task primitive 而不實作 PTGR 全套（SIC-JS 也能在無 PTGR 的系統使用）。
```

## §17.2 PTGR 五大行為承諾 [FROZEN]（行為層，非 SIC-JS schema）

```
C1 持久承諾：session 結束不忘未完成任務
C2 客觀完成：completed 必須安安確認（D-008）
C3 強制檢查：物理事實前最後一步必須 check（初階架構）
C4 提議分權：AGI 提議、安安裁定，AGI 不可自行改 task.status
C5 不刪除  ：遺忘 = 層次轉移，記錄永久保留
```

三層記憶：Active（pending/in_progress，每輪掃）→ Background（archived，可召回）→ Archive（completed/dismissed，永久）。
AGI 四種提議（不可單方面執行）：archive / revise / prompt / dismiss。格式：「[task_id] 描述，建議動作，等安安裁定」。

## §17.3 解耦邊界

```
SIC-JS 層面（格式規則，使用 task 即適用）：
  - deliverable 不可空
  - status 轉移須合法
  - completed 須有 evidence（Format B 驗證）
  - task_id 不變性

PTGR 層面（行為協議，不寫進 SIC-JS schema）：
  - 三層記憶、強制 check 觸發時機、AGI 提議機制、工作量梯度
```

## §17.5 PTGR v0.5 PRE-EXECUTION CHECK `[v3.0 新增，T-DRIFT-5 三層修補]`

**觸發時機**：任何 agent 在執行與 task 相關的動作前，必須先完成本 check。

```
T-DRIFT-5 三層根因對應修補：

根因一：換版 rationale 沒傳遞
根因二：缺 pre-execution check  ← 過去只修了這層
根因三：IDDP 缺 supersedes / depends_on_output_of 欄位
```

### 三步驟驗證流程

**步驟一 — 修補根因一（rationale）**
```
讀取目標 task 最新的 IDDP 訊息，確認：
  □ task 版本有無更新？（查 IDDP supersedes 欄位，U-2 實作後可自動）
  □ 如果版本更新：版本變更的理由是什麼？
  □ 如果無法取得 rationale → 停止，發事件，等安安裁定，不執行
```

**步驟二 — 修補根因二（pre-execution check 本體）**
```
確認 task 的現態是最新且合法的：
  □ task_id 在持久層存在且唯一（無衝突）
  □ task.status 允許執行（pending 或 in_progress）
  □ task.created_round ≤ 當前 round
  □ task.deliverable 非空
任一失敗 → 停止，發事件，等安安裁定，不執行
```

**步驟三 — 修補根因三（IDDP 依賴欄位）**
```
確認上游依賴有無完成：
  □ 讀 IDDP 中的 depends_on_output_of 列表
  □ 對應 task 全部為 completed 或 archived → 可繼續
  □ 有任何 depends_on_output_of 的 task 未 completed → 停止，發事件，等安安
  ⚠️ 此步驟在 IDDP U-2 欄位實作前靠人工確認
```

**全部通過 → 執行**
**任一失敗 → 停止**，不執行，記錄如下：

```json
{
  "sic_version": "3.0",
  "round": 1,
  "entity": { "name": "德德", "model": "Claude Sonnet 4.6" },
  "state": {
    "context": "pre_execution_check",
    "current_action": "執行前驗證 task A-3",
    "tone": "audit"
  },
  "relation": { "user": "安安", "upstream": null },
  "event": {
    "timestamp": "2026-05-31T00:00:00+08:00",
    "description": "PRE-EXECUTION CHECK FAILED: task A-3 步驟一 rationale 未取得，等安安裁定",
    "trigger": "pre_execution_check_failed"
  },
  "intent": {
    "user_intent": "執行 task A-3",
    "system_intent": "等 rationale 確認後才能執行",
    "core_question": "安安，task A-3 版本 v2 的變更理由是什麼？"
  }
}
```

## §17.4 v2.0 → v3.0 遷移指南

```
不需遷移：只記單 session 快照、不需跨 session 任務持久 → 繼續用 2.0
需要升版：需跨 session 追蹤未完成任務、需明確完成邊界、實作 PTGR → 新記錄用 "3.0" + task

步驟：
1. 含 task 的記錄升 sic_version="3.0"
2. 既有持久任務補建 task（回填 created_round、補 deliverable 不可空、設 status）
3. 從 state.pending 升格 task（pending 可保留或改引用 task_id）
4. validator 接受 "3.0"
5. 舊 "2.0" 記錄不需改（向前相容）

**重構蒸餾慣例（2026-05-30 V5/V6 現場發現）**：
若用 v3.0 格式對既有對話做歷史重構蒸餾（task primitive 在對話期間尚未存在），建議在 event.description 加標記：
`[RECONSTRUCTED: pre-task-era, session=N, rationale=蒸餾者推斷依據]`
這不改變格式合法性（§1.7 不驗此欄位），但讓讀者知道這是重構紀錄而非當時的 real-time 記錄。
```

---

# PART 18：不要做的事

1. 不要跳過 SIC-JS 輸出（Round 7 證明）
2. 不要把 entity.name 寫成別人的名字
3. 不要修改凍結常數
4. 不要把 v2.0 key 搞混成 v1.0（沒有 memory、沒有 meta）
5. 不要在 Format A 加 confidence
6. 不要 session 結束不寫 handoff（E07 = 🔴）
7. 不要引用舊 Babel 壓縮鏈
8. 不要混用 entropy_est 和 S★ 閾值
9. 不要用 VCE stability_score 替代 S★ 做 Gate 決策
10. 不要在 SIC-JS 自創欄位
11. 不要把 SFT 理論 primitive 直接當 SIC-JS 工程欄位（用 PART 4 映射）
12. 不要跳過 BAP 五反模式掃描

**v3.0 新增**：

13. 不要用 round 號碼當 task 唯一識別符（用 Series-Serial）
14. 不要在 deliverable 為空的情況下建立 task
15. 不要 AGI 單方面標記 completed（必須安安確認）
16. 不要修改 task.id 或 task.created_round（不變性原則）
17. 不要在 task 物件存在時設 task: null（要麼省略整個物件，要麼完整）
18. 不要把 PTGR 行為規則（三層記憶、check 觸發時機等）寫進 SIC-JS schema 欄位（解耦）
19. 不要用 sic_version:"2.0" 的記錄含 task 欄位（用 task 必須升 "3.0"）
20. 不要把 task 持久層存儲邏輯（SQLite 等）混入 SIC-JS 格式規範（存儲是 PTGR 的事）

---

**文件結束。**

**如果你的實作跟本檔案矛盾，停下來標記 [CONFLICT WITH REFERENCE]，不要自己解決。**

---

**SIC-JS 3.0 核心原則**：

```
v2.0 五原語描述「此刻是什麼」(is)；v3.0 task 描述「應當成為什麼」(ought)
task_id 永遠短小（A-1），round 可到天文數字
deliverable 是 completed 的唯一合法判據
completed 必須雙方確認，不是單方面宣稱
遺忘是層次轉移，不是刪除
跨 agent 靠 upstream sha，不在 SIC-JS 新增規則
SIC-JS 是格式規範，不是行為協議；task 是第六原語，不是 event 子欄位；PTGR 主角，SIC-JS 配角
```

*基底：SICJS_V2_TECHNICAL_ORIGINAL_REFERENCE_v2.1_FINAL（逐字繼承）*
*整合：德德（Claude Sonnet 4.6），2026-05-31 — File_2026_5_31*
*設計者：安安（Andwar Cheng），Protocol Seeder*
*語言狀態：🟡 中文母本；EN 平行版待母本封版後產出（元則八）*

---

## 封版聲明（Sealing Declaration）

```
狀態：PENDING — 等安安（Protocol Seeder）+ 老翔 + 德德 三方確認後封版
文件 SHA256：f844d81293a2c368b5f90d0db314a1bf3701426b629fefada5e52243345cc3e9
Schema SHA256：d9835f7fb37f70b69290140c49f8729b6fb247092f933e00d5f7d34817fcbfbb
封版時機：B（等 OPEN-8 repo 建立 + OPEN-5 Babel 更新後）
封版方法：三方確認後，以 sha256 鎖定本 .md 檔案，hash 值即為 v3.0 canonical 識別符
```
