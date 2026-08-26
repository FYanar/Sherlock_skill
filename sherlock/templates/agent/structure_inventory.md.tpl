# {{PROJECT_NAME}} — Kod Envanteri ve Sembol Haritasi

Schema-Version: 3.0
Snapshot-Date: {{DATE_SLUG}}
Inventory-Status: VERIFIED

Bu dosya proje içerisindeki tüm modüllerin, sınıfların, fonksiyonların ve CLI parametrelerinin ayrıntılı sembol haritasıdır.

## 1. Modül ve Sembol Detaylari

### Modül: `tools/run_mcp.py`
- **Rol:** MCP stdio sunucusu başlatıcı launcher.
- **Fonksiyonlar:**
  - `main()`: `Agent.knowledge_base.cli` üzerinden MCP sunucusunu veya CLI araçlarını çalıştırır.

---

## 2. CLI Giris Noktalari ve Parametreler

- `python tools/run_mcp.py status`: Bilgi tabanı istatistiklerini görüntüler.
- `python tools/run_mcp.py ingest`: Artımlı indeksleme yapar.
- `python tools/run_mcp.py mcp`: MCP stdio sunucusunu başlatır.
