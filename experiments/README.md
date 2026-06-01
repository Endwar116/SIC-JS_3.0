# SIC-JS v3.0 實驗數據（Evidence Base）

這個目錄包含 SIC-JS v3.0 工程基線測試的原始數據與代碼。

## 實驗定位

這些是「參考實作的工程驗證（Engineering Validation）」，不是「SIC-JS 假說的科學驗證（Scientific Validation）」。

工程驗證確認：格式正確、系統穩定、安全基線成立。科學驗證（A/B 對照實驗）需要真實多模型數據，目前受算力限制，是我們申請外部計算資源的主要理由。

## 關鍵數字

| 指標 | 數字 | 來源 |
|------|------|------|
| 語義驗證開銷 | 0.097ms P50 | FS-B-2 rigorous/report_async.json |
| XSS 穿透率 | 0% | FS-B-5 rigorous (1,000 mutation, 0 bypass) |
| 記憶體成長 | growth_factor=1.07 | FS-B-4 rigorous report |
| Validator 吞吐 | 220 rps | FS-B-1 rigorous (10,006 fuzz inputs) |
| 100 concurrent P99 | 84ms (asyncio) | FS-B-2 rigorous/report_async.json |

## 目錄結構

```
experiments/
├── FS-B-1/   ← Validator CLI (8/8 test cases)
├── FS-B-2/   ← NDJSON Streaming Server (TTFB benchmark)
├── FS-B-3/   ← SQLite Task Ledger (9/9 test cases)
├── FS-B-4/   ← Web Components Dashboard (TTR benchmark)
├── FS-B-5/   ← Enterprise Security Stack (10/10 XSS blocked)
└── rigorous/ ← 嚴謹版實驗（Fuzz / Concurrent / Chaos / Mutation）
    ├── FS-B-1/   ← 10,006 筆 Fuzz + Boundary
    ├── FS-B-2/   ← 100 併發 + P50/P95/P99 + Chaos
    ├── FS-B-3/   ← 100 線程 + 狀態機窮舉 + 損壞恢復
    ├── FS-B-4/   ← 10,000 cards + Memory + Reflow Storm
    └── FS-B-5/   ← 1,000 XSS 變異 + Bypass 嘗試
```

## 測量環境

- OS: Ubuntu 22.04 (linux/amd64)
- Python: 3.11.0rc1
- Server: uvicorn + FastAPI (single-process asyncio)
- Hardware: Cloud sandbox (shared CPU, ~2GB RAM)
- Network: localhost loopback (no network latency)
