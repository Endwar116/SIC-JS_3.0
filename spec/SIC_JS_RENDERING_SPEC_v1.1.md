# SIC-JS Rendering Specification v1.1 (祖檔級工程規格書)

**Document Level**: Engineering Specification (工程規格書)
**Status**: REVIEW COMPLETE (RC)
**Date**: 2026-06-01
**Author**: Manus AI (Chief Web Architecture Engineer)
**Alignment**: Strictly aligned with `SICJS_30_技術原始記載檔_完整自足_File_2026_5_31.md` and `sic-js-schema-v3.0.json`.

---

## Part 1: Protocol Layer (協議層約束)

本規格書定義了 SIC-JS 狀態如何渲染為 HTML DOM。在進入任何渲染邏輯之前，所有資料必須通過協議層的絕對約束。

### 1.1 The Six Primitives (六原語映射基礎)

渲染引擎必須能夠處理 SIC-JS v3.0 的六個原語。其中 `task` 屬於 ought 層（持久），其餘五個屬於 is 層（快照）。

| Primitive | Rendering Strategy (渲染策略) | DOM Representation (DOM 表現) |
|-----------|-------------------------------|-------------------------------|
| `task` | **Persistent Node** (持久節點) | `<sic-task id="A-1">` |
| `entity` | **Context Provider** (上下文提供者) | `<sic-entity name="德德">` |
| `state` | **Reactive Content** (響應式內容) | `<sic-state data-action="...">` |
| `relation`| **Graph Edge** (圖結構邊緣) | `<sic-relation upstream="...">` |
| `event` | **Transient Toast/Log** (瞬態提示) | `<sic-event>` (可選渲染) |
| `intent` | **Semantic Wrapper** (語義包裝) | `<sic-intent>` (通常隱藏，供除錯) |

### 1.2 The Invariants (不變性約束)

渲染引擎的效能最佳化（如 S-VDOM）**必須且只能**建立在以下官方凍結的約束之上：

1. **Task ID 不變性 `[FROZEN]`**：
   - `task.id` 一旦分配，絕對不可更改。
   - 格式必須符合 Series-Serial：`^[A-Z]+-[A-Z]{1,2}-[1-9][0-9]{0,2}$` 或無前綴版本。
   - **渲染層紅利**：渲染引擎可安全地將 `task.id` 作為 DOM 節點的 Stable Key，實現 O(1) 尋址，無需進行樹狀 Diffing。

2. **Task Status 閉集合 `[FROZEN]`**：
   - `task.status` 必須屬於 `{pending, in_progress, completed, dismissed, archived}`。
   - **渲染層紅利**：UI 元件可預先編譯這五種狀態的 CSS 樣式與過場動畫，無需處理未知的狀態字串。

3. **Created Round 不變性 `[FROZEN]`**：
   - `task.created_round` 絕對不可更改，且必須 `≤ round`。
   - **渲染層紅利**：可用於列表的絕對穩定排序（Stable Sorting）。

### 1.3 Schema Validation (Schema 驗證)

任何進入渲染管線的 JSON Payload，必須先通過 `sic-js-schema-v3.0.json` 的驗證。
- **Fail-Closed 原則**：驗證失敗的 Payload 必須被丟棄，**絕對不可**進入渲染層，以防止 XSS 或 DOM 污染。
- **Semantic Rupture 處理**：若 `state.current_action` 為 null（Schema 允許但標記為 WARN），渲染層應顯示視覺警告（如紅色虛線框），提示語義斷裂。

---

## Part 2: Runtime Layer (執行時管線規格)

依據官方裁定（D-006），PTGR (Persistent Task Governance Runtime) 是主角，SIC-JS 是配角。渲染引擎的 Runtime Layer 必須實作 PTGR 的行為承諾，並作為 SIC-JS 狀態與 DOM 之間的中介。

### 2.1 The WASM Validator (WASM 驗證器)

為了確保企業級安全（防止前端 JS 篡改狀態），Runtime Layer 的核心驗證邏輯應編譯為 WebAssembly (WASM)。

- **輸入**：NDJSON Streaming 或 WebSocket 傳來的 SIC-JS Payload。
- **處理**：
  1. 執行 JSON 解析（在 WASM 記憶體沙盒內）。
  2. 執行 `sic-js-schema-v3.0.json` 驗證。
  3. 執行 PTGR 狀態轉移合法性檢查（例如：不可從 `completed` 轉回 `in_progress`）。
- **輸出**：驗證通過後，透過 SharedArrayBuffer 或 Signals 機制，將狀態變更通知 Rendering Engine Layer。

### 2.2 PTGR Behavior Implementation (PTGR 行為實作)

Runtime Layer 必須在前端實作以下 PTGR 承諾：

1. **C2 客觀完成 (Completed Validation)**：
   - 當 AGI 傳來 `status: "completed"` 的 Payload 時，Runtime 必須攔截該狀態。
   - UI 應顯示為「等待安安確認 (Pending User Confirmation)」。
   - 只有在使用者（安安）透過 UI 點擊確認後，Runtime 才會將最終的 `completed` 狀態寫入持久層並更新 DOM。

2. **C4 提議分權 (Proposal Delegation)**：
   - AGI 發出的 `archive`, `revise`, `prompt`, `dismiss` 提議，在 Runtime 中應被解析為「待處理的 UI 任務（Action Items）」，而非直接修改底層狀態。

3. **PRE-EXECUTION CHECK (執行前驗證)**：
   - 這是修補 T-DRIFT-5 的關鍵。
   - Runtime 在允許 AGI 繼續執行任務前，必須在 UI 上強制顯示檢查清單：
     - [ ] 版本變更理由 (Rationale)
     - [ ] Task 現態合法性
     - [ ] 上游依賴 (depends_on_output_of) 是否完成
   - 若檢查失敗，Runtime 應阻擋 AGI 的後續操作，並在 UI 標示紅旗。

---

## Part 3: Rendering Layer (渲染層規格)

渲染層負責將 Runtime 驗證過的狀態轉換為 DOM。本規格書定義了 **S-VDOM (Semantic Virtual DOM)** 作為標準渲染引擎。

### 3.1 S-VDOM: O(1) Stable Key Routing

傳統 React VDOM 在處理列表時，依賴開發者手動提供 `key` 屬性，否則會觸發昂貴的樹狀掃描。S-VDOM 利用 SIC-JS v3.0 的協議約束，從根本上消除了這個問題。

- **機制**：
  1. S-VDOM 內部維護一個 `Map<task_id, DOMNode>`。
  2. 當收到新的 SIC-JS Payload 時，直接讀取 `task.id`。
  3. 透過 Hash Map 進行 O(1) 尋址，直接找到對應的 DOM 節點。
  4. 僅對該節點的子樹進行局部更新（如更新 `task.status` 對應的 CSS class）。
- **效能指標**：此機制將 TTR (Time to Render) 從 O(N) 降至 O(1)，是 Cerebras Zero-Latency Stack 的核心基礎。

### 3.2 Signals-based Reactivity (細粒度響應式)

對於 `state` 原語中的高頻變動欄位（如 `state.current_action`），S-VDOM 應採用 Signals 架構。

- **機制**：
  - 將 `state.current_action` 綁定為一個 Signal。
  - 當 WASM Validator 解析出新的 `current_action` 字串時，直接透過 SharedArrayBuffer 更新 Signal 的值。
  - 綁定該 Signal 的 DOM TextNode 會被直接修改（`node.textContent = newValue`），完全繞過 VDOM 的 Diffing 階段。

### 3.3 The Four-Layer DOM Metaphor (四層 DOM 映射)

渲染層的 DOM 結構必須反映 SIC-JS 的系統工程理論（參考 P13）：

1. **Core Layer (核心層)**：
   - 不在 DOM 中，存在於 WASM 記憶體。
2. **Canonical Layer (典範層)**：
   - 實作：`mode: 'closed'` 的 Shadow Root。
   - 內容：包含核心的語義資料（如 `data-task-id`, `data-status`），外部 CSS/JS 絕對無法存取或修改。
3. **Toolkit Layer (工具層)**：
   - 實作：Web Components (`<sic-task>`)。
   - 內容：提供標準的 API 與 Event Emitters，供上層呼叫。
4. **Profile Layer (表現層)**：
   - 實作：Light DOM 與 `<slot>`。
   - 內容：開發者自定義的 CSS 樣式、排版與動畫。

這種映射確保了「語義的絕對安全（Canonical）」與「視覺的絕對自由（Profile）」並存。

---

## Part 4: Security & Governance (安全與治理規格)

SIC-JS 不僅是資料格式，更是 AGI 治理的基礎設施。渲染層必須與 Babel 壓縮鏈及 Gate Chain 深度整合，確保 UI 呈現的狀態是絕對安全且合規的。

### 4.1 Babel & Gate Chain Integration (治理鏈整合)

依據官方規格 §5.3，Babel always wins。渲染層必須實作以下防禦機制：

1. **Gate Hard Block 攔截**：
   - 當 WASM Validator 偵測到 `task.status` 變更為 `dismissed`，且 `event.trigger` 包含 Gate 阻擋資訊時。
   - **UI 行為**：強制中斷該任務的所有動畫與互動，將卡片標示為紅色（或自定義的警告樣式），並在顯眼處顯示 `event.description` 中的阻擋原因。
   - **狀態鎖定**：此時該 DOM 節點進入終態（Terminal State），拒絕任何後續的狀態更新，直到安安介入裁定。

2. **BAP 五反模式掃描**：
   - 任何 AGI 提報的 `completed` 狀態，若其 `evidence` 觸犯 BAP 五反模式（如「語義上已完成」、「之後補實驗」）。
   - **UI 行為**：WASM Validator 應直接拒絕該狀態轉移，UI 維持 `in_progress`，並觸發一個 `semantic_rupture` 警告。

### 4.3 Idempotent Write (冪等寫入與防篡改)

在 Enterprise SDK 中，為了防止外部腳本或 DevTools 手動篡改 DOM（例如修改 `data-status`），渲染引擎**不使用** `MutationObserver` 來監聽並 Rollback。

正確的防篡改機制是 **Idempotent Write（冪等寫入）**：
- 每次 WASM 驗證器輸出新的合法狀態時，渲染引擎直接將該狀態覆蓋到 DOM 上。
- 沒有「Rollback」的概念，只有「下一個正確狀態覆蓋之前的任何狀態」。
- 如果外部 JS 惡意修改了 DOM，WASM 驗證完下一個 SIC-JS round 時，會自動將正確的狀態蓋回去。
- **優勢**：避免了 `MutationObserver` 與 Closed Shadow Root 之間的衝突，確保單向語義流的絕對純潔性。

### 4.2 The MutationObserver Red Flag (雙向綁定紅旗)

在 P8 論文中探討的 `MutationObserver Sync`（透過修改 DOM 屬性逆向更新 SIC-JS 狀態），在企業級治理中被標記為 **[UNSAFE]**。

- **企業環境禁用**：在 Enterprise SDK 中，此功能必須被強制關閉。任何試圖從 DOM 反向修改狀態的行為，都應被視為潛在的 XSS 攻擊或越權操作。
- **單向語義流 (One-way Semantic Flow)**：合法的狀態變更**只能**遵循以下路徑：
  `AGI Output -> NDJSON -> WASM Validator -> S-VDOM -> DOM`
- **開發者環境豁免**：僅在 Developer SDK 的 Debug 模式下，允許開啟此功能以方便快速測試狀態機。

---

## Part 5: SDK Interface & Product Matrix (SDK 介面與產品矩陣)

為了讓不同場景的開發者能順利接入 SIC-JS 渲染管線，本規格書定義了三大 SDK 產品線的介面標準。

### 5.1 The Three SDK Tiers (三大 SDK 產品線)

| SDK 產品線 | 目標客群 | 核心技術組合 | 效能等級 | 安全等級 |
|------------|----------|--------------|----------|----------|
| **Developer SDK** | 獨立開發者、Dashboard 雛形 | S-VDOM + Open Shadow Root + MutationObserver (可選) | 高 | 低 (允許雙向綁定) |
| **Enterprise SDK** | 企業級應用、高合規性系統 | WASM Validator + Closed Shadow Root + 單向語義流 | 極高 | 極高 (物理級防篡改) |
| **Cerebras SDK** | AI 原生硬體、極限效能場景 | NDJSON Streaming + WASM + Signals Reactivity | 理論極限 | 高 |

### 5.2 Standard API Interface (標準 API 介面)

無論底層使用哪種 SDK，對外暴露的 API 必須保持一致，以符合「Toolkit Layer」的抽象。

```typescript
// 核心初始化
import { SicRuntime } from '@sic-js/enterprise-sdk';

const runtime = new SicRuntime({
  mode: 'strict', // 強制單向語義流
  container: document.getElementById('app')
});

// 註冊自定義渲染器 (Profile Layer)
runtime.registerProfile('task-card', (task, state) => {
  return `
    <div class="card status-${task.status}">
      <h3>${task.id}: ${task.title}</h3>
      <p>Action: ${state.current_action}</p>
    </div>
  `;
});

// 接收 NDJSON 串流
fetch('/api/sic-stream').then(response => {
  runtime.consumeStream(response.body);
});

// 監聽 PTGR 治理事件
runtime.on('proposal_required', (proposal) => {
  // 觸發 UI 讓安安裁定 (C4 提議分權)
  showApprovalDialog(proposal);
});
```

### 5.3 Custom Elements Specification (自定義元素規範)

SDK 必須自動註冊以下 Web Components，供不寫 JS 的純 HTML 開發者使用：

- `<sic-provider src="/api/stream">`：建立 Runtime 上下文並連接資料源。
- `<sic-task id="A-1">`：綁定特定 Task ID，內部自動套用 S-VDOM 路由。
- `<sic-state field="current_action">`：綁定特定狀態欄位，內部自動套用 Signals 響應式更新。

---

## Part 6: Benchmarking & Conformance (測試與合規規格)

為了確保各家實作的渲染引擎達到「國際 Runtime 基礎設施」的標準，本規格書定義了標準化的效能測量指標與合規性測試（Conformance Test）。

### 6.1 Performance Metrics (效能指標)

任何宣稱支援 SIC-JS 的渲染引擎，必須公開以下三項指標的測試結果：

1. **TTFB (Time to First Byte)**：
   - **定義**：從發出請求到收到第一個 NDJSON Chunk 的時間。
   - **標準**：必須 < 50ms（依賴網路層，但引擎必須支援 Chunked 串流解析）。
2. **TTR (Time to Render)**：
   - **定義**：從 WASM Validator 輸出合法狀態，到 `requestAnimationFrame` 觸發的時間。
   - **標準**：
     - `TTR < 2ms`：DOM 層 O(1) S-VDOM 節點更新（dom_construction P99）。
     - `TTR < 16ms`：含 parsing + streaming 的 end-to-end pipeline TTR。
3. **JFI (Jank-Free Index)**：
   - **定義**：在每秒 1000 次狀態更新的高頻負載下，主執行緒維持 60fps 的比例。
   - **標準**：
     - `JFI > 99%`：限 Signals 路徑（SharedArrayBuffer 直接寫 DOM）。
     - `JFI > 95%`：S-VDOM 路徑（有 Map lookup 開銷）。

### 6.2 Conformance Test Suite (合規性測試套件)

實作必須通過以下「六大防禦測試」，否則視為不合規（Non-compliant）：

| 測試 ID | 測試場景 | 預期行為 |
|---------|----------|----------|
| `CT-01` | 傳入 `task.id` 格式錯誤的 Payload | WASM 攔截，不觸發任何 DOM 更新。 |
| `CT-02` | 傳入 `task.status` 為未定義字串 | WASM 攔截，不觸發任何 DOM 更新。 |
| `CT-03` | AGI 單方面傳入 `status: "completed"` | UI 顯示 Pending Confirmation，底層狀態不變。 |
| `CT-04` | 傳入 `state.current_action: null` | 允許渲染，但 UI 必須觸發 `semantic_rupture` 視覺警告。 |
| `CT-05` | 透過 DevTools 手動修改 DOM 的 `data-status` | (Enterprise SDK) 狀態不變，下一個 round 自動覆蓋恢復 DOM (Idempotent Write)。 |
| `CT-06` | 執行前驗證 (PRE-EXECUTION CHECK) 失敗 | 阻擋後續操作，UI 顯示紅旗。 |

---

**Document End.**
**Status**: REVIEW COMPLETE (RC) -> READY FOR REVIEW
**Next Step**: 提交安安與德德進行架構審查。
