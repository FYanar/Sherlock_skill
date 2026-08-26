---
name: goal-verifier
description: Formal Goal and Evidence Verification Methodology for Sherlock.
---

# Sherlock Goal & Evidence Verifier (Adli Tıp Kanıt Doğrulama Metodolojisi)

`goal-verifier`, öne sürülen iddiaları, tamamlanmış sayılan iş paketlerini ve test çıktılarını körlemesine kabul etmek yerine **ham disk artefaktları, çıkış kodları, loglar ve Bayesçi olasılık güncellemeleriyle** adli tıp düzeyinde doğrulayan kanıt denetleme motorudur.

---

## 1. Dört Aşamalı Doğrulama Protokolü (V-CYCLE)

```text
[İddia / Bulgu / Hedef]
         │
         ▼
[1. Hedef Ayrıştırma & Kabul Kriteri Çıkarma]
         │
         ▼
[2. Ham Kanıt & Disk Artefaktı Taraması (SHA-256, Log, Exit Code)]
         │
         ▼
[3. Yanlışlanabilirlik & Stres Testi (Falsifier Execution)]
         │
         ▼
[4. Bayesçi Kanıt Damgalaması -> CONFIRMED | REFUTED | UNVERIFIABLE]
```

---

## 2. Doğrulama Adımları

### Adım 1 — Hedef ve İddia Ayrıştırma (Goal Decomposition)
Her iddia (`C1..Cn` veya `F-S / F-L / F-A / F-C / F-T` bulguları) için:
1. **İddianın Doğrudan İfadesi:** Ne iddia ediliyor? (Örn: "X fonksiyonu hata fırlatmadan None dönüyor").
2. **Beklenen Somut İz:** Bu iddia doğruysa dosya sisteminde veya loglarda hangi spesifik bayt dizilimi, anahtar veya çıktı bulunmalıdır?
3. **Kabul Eşiği:** İddianın doğrulanması için gereken asgari kanıt seviyesi nedir?

### Adım 2 — Ham Disk ve Artefakt Denetimi (Zero-Trust Inspection)
Araştırmacı ajanların özetlerine veya iddialarına güvenilmez; doğrudan dosya sistemi incelenir:
1. **Kaynak Kod Kontrolü:** Belirtilen `dosya:satır` okunarak ifadenin varlığı teyit edilir.
2. **Çıkış Kodları ve Log Bütünlüğü:** `outputs/logs/` altındaki taze loglar taranır, hata/uyarı izleri ve zaman damgaları doğrulanır.
3. **SHA-256 Hash Bütünlüğü:** Kritik dosyaların SHA-256 hash'leri hesaplanarak beklenmeyen bir mutasyon olup olmadığı doğrulanır.
4. **Şema & Veri Uyumu:** JSON/YAML/CSV çıktılarında sözleşmeye aykırı eksik alan, `NaN` veya geçersiz tip olup olmadığı denetlenir.

### Adım 3 — Yanlışlanabilirlik Sınaması (Falsifier Testing)
Bulguda verilen `falsifier` alanı test edilir:
- Eğer yanlışlama testi çalıştırıldığında iddia çöküyorsa $\to$ `REFUTED`.
- Eğer yanlışlama testi iddianın haklılığını kanıtlıyorsa $\to$ `CONFIRMED`.

### Adım 4 — Bayesçi Damgalama ve Raporlama
`thinking-bayesian` ilkeleriyle:
- **`CONFIRMED`:** Bizzat okunan satır, taze komut çıktısı veya deterministik disk artefaktı ile %100 kanıtlanan durumlar.
- **`REFUTED`:** Somut karşı-kanıtla yanlışlığı ispatlanan durumlar (gerekçesiyle birlikte kaydedilir).
- **`UNVERIFIABLE`:** Ortam kısıtları, eksik loglar veya test edilemeyen dış bağımlılıklar nedeniyle bağımsız teyit edilemeyen durumlar.

---

## 3. Raporlama Şablonu (`15-r1-verification.md`)

```markdown
# 1. Tur Adli Tıp Kanıt Doğrulama Raporu (15-r1-verification.md)

## Kanıt Denetim Tablosu

| Bulgu Kimliği | İddia Konumu (Locus) | Araştırmacı Güveni | Verifier Damgası | Doğrulama Kanıtı / Karşı Kanıt |
|:---:|---|:---:|:---:|---|
| **F-S1** | `scripts/protein_prep/pdb_repair.py:112` | CONFIRMED | **CONFIRMED** | Satır okundu: `MockFixer` dunder metodu eksiksiz. |
| **F-A2** | `scripts/docking/zbg_runtime.py:45` | PLAUSIBLE | **REFUTED** | Komut koşturuldu: Zn atomu için koordinat doğru bağlandı. |
| **F-C1** | `config.yaml:12` | SPECULATIVE | **UNVERIFIABLE** | İlgili log dosyası diskte bulunamadı. |
```