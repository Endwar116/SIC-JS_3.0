# Quick Start — 5 分鐘上手 SIC-JS v3.0

## 1. Clone the repository

```bash
git clone https://github.com/Endwar116/SIC-JS_3.0.git
cd SIC-JS_3.0
```

## 2. Validate a SIC-JS record

```bash
cd packages/core/validator
pip install jsonschema>=4.22.0
python3 sic_validate.py fixtures/T2_v3_valid_task.json
# → PASS: sic-js-schema-v3.0.json validated.
```

## 3. Start the streaming server

```bash
cd packages/server
pip install -r requirements.txt
uvicorn server_async:app --host 0.0.0.0 --port 8080
```

## 4. Open the dashboard

Open your browser and navigate to `http://localhost:8080`. You will see the SIC-JS dashboard rendering task cards in real-time from the NDJSON stream.

## 5. Run the full test suite

```bash
# From the repository root
bash integration_test.sh
# Expected output: All Integration Tests PASS
```

## What just happened?

You have just:
1. Validated a SIC-JS v3.0 record against the official JSON Schema
2. Started an async NDJSON streaming server that serves validated records
3. Opened a Web Components dashboard that renders those records in real-time

## Next steps

- Read the [Protocol Specification](../spec/SICJS_30_技術原始記載檔.md) for the full protocol details
- Read the [Schema Reference](schema-reference.md) for field-by-field documentation
- Read the [Rendering Specification](../spec/SIC_JS_RENDERING_SPEC_v1.1.md) for how to build your own renderer
- Check the [examples/](../examples/) directory for more usage patterns
