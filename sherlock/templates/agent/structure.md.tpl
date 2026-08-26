# {{PROJECT_NAME}} — Güncel Proje Modüler Yapisi

Schema-Version: 3.0
Inventory-Snapshot-Date: {{DATE_SLUG}}
Inventory-Status: VERIFIED_SNAPSHOT

Bu belge projenin güncel mimari haritasidir. Kod gerçegi her zaman dokümandan üstündür.

## 1. Modüler Paket Mimarisi ve Dosya Dagilimi

| Alt Paket / Dizin | Dosya Sayisi | Toplam Satir | Rol ve Sorumluluk |
|---|:---:|:---:|---|
| `src/` veya `scripts/` | 1 | ~50 | Çekirdek uygulama modülleri |
| `tools/` | 1 | ~30 | Geliştirici & Ajan Yardımcıları (`run_mcp.py` MCP Server Launcher) |
| `tests/` | 1 | ~40 | Birim ve entegrasyon testleri |
| `Agent/` | 7 | ~500 | Proje anayasası, hafıza ve durum belgeleri |

## 2. Test ve Dogrulama Durumu
- **Test Süiti:** Başlangıç testleri hazır.
- **Hedef:** %100 Başarı ve Anti-Paper-Tiger kalkanı.
