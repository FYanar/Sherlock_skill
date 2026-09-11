# {{PROJECT_NAME}} — Proje Hafizasi ve Mimari Degismezler

Schema-Version: 3.0
Snapshot-Date: {{DATE_SLUG}}
Memory-Budget: <= 1.000 Lines (FIFO Pruning Enforced via scripts/memory_manager.py --prune)
Scoring: her ders <!-- score:Lxxx uses:N fails:M status:ACTIVE|DEPRECATED --> taşır. 3 fail → DEPRECATED. Budamada DEPRECATED önceliklidir; arşiv Agent/memory_archive/ altındadır, asla silinmez.

> [!IMPORTANT]
> **Düşünme Öncesi Zorunlu Hafıza Okuma Kuralı:**
> Sherlock ve tüm alt ajanlar, herhangi bir hipotez kurmadan, plan yapmadan veya kod yazmadan önce bu dosyayı **tam okur**.
> Geçmişte yapılan işlemler, uygulanan yaptırımlar, alınan çıktılar ve çıkarımlar incelenerek aynı hataların tekrarlanması önlenir.

---

## 1. Mimari Degismezler ve Sistem Kurallari

1. **Katı Hiyerarşi & Tekil Sorumluluk:**
   - Modüller tekil sorumluluk ilkesine (SRP) göre dizayn edilir; her dosya $\le 1.400$ satır olmalıdır.
2. **Anti-Duplikasyon Kalkanı:**
   - Yeni fonksiyon yazılmadan önce AST ve sembol taraması yapılır; mevcut fonksiyonlar genişletilir, mükerrer kod üretilmez.
3. **SSOT (Tek Doğruluk Kaynağı):**
   - Ortak yardımcılar çekirdek modüllerde toplanır (`core/` vb.).
4. **Modüler Dizin Standardı:**
   - Yardımcı araçlar ve scriptler kök dizine yığılmaz; `scripts/` veya `tools/` dizininde modüler olarak tutulur.

---

## 2. Tamamlanan Is Paketleri ve Deneyim Günlügü (Completed Work Packages & Experience Log)

| Is Paketi / Vaka | Yapilan Islem & Kapsam | Durum | Alinan Çikti & Dogrulama Sonucu | Kök Neden Çikarimi & Ögrenilen Çözüm Yolu | Skor |
|:---|:---|:---:|:---|:---|:---:|
| **WP-00**<br>Inception & Anayasa Kurulumu | `code.md` ve `Agent/` altyapısının Sherlock ile otomatik inşası. | **BAŞARILI** | Tüm zorunlu belgeler eksiksiz kuruldu. | Sağlam anayasal temel ve modüler yapı, projenin büyümesinde teknik borcu engeller. | <!-- score:L000 uses:1 fails:0 status:ACTIVE --> |

---

## 3. Kod ve Bilesen Kök Neden Çikarimlari (Root Cause & Lessons Learned)

1. **Modüler Parçalama:** Monolitik dosyaların alt paketlere bölünmesi bağımlılıkları izole eder ve test edilebilirliği artırır.
2. **Fail-Closed İlkesi:** Hatalar `try/except: pass` ile gizlenmemeli; doğrulanabilir hata ve log üretilmelidir.
3. **Diskte Kalıcı Dava Mührü:** Her teknik analiz sonucunda `.sherlock/YYYYMMDD-<vaka>/` klasörü açılmalı ve `40-verdict.md` yazılmalıdır.

---

## 4. Sherlock Adli Tip ve Dava Hafizasi (Case Registry)

- **Dava 0:** `.sherlock/{{DATE_SLUG}}-project-inception/` (Hüküm: `INITIAL_SYSTEM_SEALED`)
