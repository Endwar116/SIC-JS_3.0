# SIC-JS Changelog

## v3.0.0 (2026-06-01)

- task primitive 第六原語（ought 層，跨 session 持久）
- PTGR v0.5 PRE-EXECUTION CHECK 三層根因
- Series-Serial task_id（含前綴支援，格式 `^[A-Z]+-[A-Z]{1,2}-[1-9][0-9]{0,2}$`）
- sic-js-schema-v3.0.json（SHA256: `d9835f7fb37f70b69290140c49f8729b6fb247092f933e00d5f7d34817fcbfbb`）
- task.status 五狀態閉集合 `[FROZEN]`：`{pending, in_progress, completed, dismissed, archived}`
- task.id 不變性 `[FROZEN]`：一旦分配絕不可更改
- task.created_round 不變性 `[FROZEN]`：必須 ≤ round
- completed 三條件同時滿足：deliverable 達成 + evidence + 雙方確認
- [v2.0 baseline] entity/state/relation/event/intent 全部繼承

## v2.0.0 (2026-01-16)

- 五原語基礎：entity / state / relation / event / intent
- sic_version 欄位引入
- round 計數器
- 向前相容設計

---

**SHA256 記錄**：
- `spec/SICJS_30_技術原始記載檔.md`：`ed7aa816e91fb0c22918dd381e57b51d950b8c78224a3482ea438ff2d6444e5a`
- `packages/core/schema/sic-js-schema-v3.0.json`：以最終入庫版本為準（見下方更新）
