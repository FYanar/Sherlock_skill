# {{PROJECT_NAME}} — Test Senaryolari ve Kabul Kriterleri

Schema-Version: 3.0
Revision: 1.0

Bu belge projenin bağımsız test oracle ve kalite kapısı sözleşmesidir.

## 1. Temel Test Kümeleri

| Test Kümesi | Dosya / Komut | Amaç | Beklenen Çıktı |
|---|---|---|---|
| **Birim Testleri** | `pytest tests/` (veya `npm test`) | Çekirdek modüllerin mantıksal doğruluğu | %100 PASS, 0 FAIL |
| **MCP Sunucu Testi** | `python tools/run_mcp.py status` | Bilgi tabanı bağlantı doğrulaması | Çıkış kodu: 0 |
| **AST & Anti-Paper-Tiger** | `pytest tests/` | Mock/sabit metin hilesi içermeyen gerçek çağrılar | Gerçek runtime doğrulaması |

## 2. Kalite Kapıları
- Hiçbir iş paketi (WP), ilgili testler yeşil olmadan `COMPLETED` olarak işaretlenemez.
- `assert "success" in text` gibi kağıt kaplan testler derhal `FAIL-PAPER-TIGER-TEST` damgası alır.
