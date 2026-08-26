# {{PROJECT_NAME}} — Aktif Calisma Plani

Schema-Version: 3.0
Plan-ID: PLAN-{{DATE_SLUG}}-INITIAL
Revision: 1.0
Target-Scope: {{PROJECT_SCOPE}}
Status: IN_PROGRESS

> [!NOTE]
> Bu belge projenin dinamik eylem planidir.
> Tamamlanan is paketleri (COMPLETED) doğrudan `Agent/memory.md` dosyasina tasinir ve buradan silinir.
> Burada yalnizca aktif, bekleyen (PENDING) veya basarisiz (FAILED) is paketleri yer alir.

---

## 1. Aktif Hedef ve Kapsam

- **Proje:** {{PROJECT_NAME}}
- **Temel Hedef:** {{PROJECT_DESCRIPTION}}
- **Yürütme Yöntemi:** TDD Odakli Modüler Gelistirme & Sherlock 6-Ajanli Denetim

---

## 2. Bekleyen Is Paketleri (Pending Work Packages)

### WP-01: Proje Temel Iskeleti ve Modüler Paket Mimarisi
- **Kapsam:** Çekirdek modüllerin, yardımcı araçların (`tools/`) ve test suite altyapısının kurulması.
- **Hedef Dosyalar:** `src/` veya `scripts/`, `tools/`, `tests/`
- **Bagimliliklar:** Yok
- **Kabul Kriteri:** Birim testlerin (`pytest` / `npm test` / `cargo test`) %100 basarili olmasi.
- **Durum:** PENDING

---

## 3. Risk ve Acil Durum Planlari

1. **Bağlantı/Bağımlılık Uyuşmazlığı:** Sanal ortam ve lockfile dosyaları taranarak kütüphane sözleşmeleri (`Context7`) doğrulanır.
2. **Mimari Aşınma:** Modüller 1.400 satırı aştığında otomatik olarak parçalanır.
