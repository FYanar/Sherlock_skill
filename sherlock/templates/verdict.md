# Hakem Heyeti Kararı (Verdict) — <dava adı>

```yaml
case:          <slug>
date:          <YYYY-MM-DD>
review_policy: standard | deep
depth:         standard | deep
rounds:        <çalıştırılan tur sayısı (en az 2, en fazla 3)>
verdict:       GO | GO-WITH-CONDITIONS | NO-GO | INSUFFICIENT-EVIDENCE
```

## 1. Nihai Karar ve Gerekçe

**<VERDICT_STAMP>** — <Tek paragraf adli tıp gerekçesi. Hangi kanıtlara dayanarak verildiği.>

## 2. Koşullar Listesi

*(Yalnızca `GO-WITH-CONDITIONS` için geçerlidir. Her koşul numaralı, ölçülebilir ve bağımsız test edilebilir olmalıdır.)*

| # | Koşul İfadesi | İlgili Bulgu(lar) | Doğrulama & Kabul Kriteri |
|:---:|---|---|---|
| K-1 | | F-S1, F-C2 | |
| K-2 | | F-A3 | |

## 3. Öncelikli Eylem Planı (20-plan.md Entegrasyonu)

`Severity × Verification Status` formülüyle sıralanmış, bağımlılık hiyerarşisine oturtulmuş iş paketleri:

| Sıra | Bulgu Kimliği | Ajan Rolü | Şiddet | Doğrulama Damgası | Eylem / Düzeltme | Bağımlılık (`depends-on`) |
|:---:|:---:|:---:|:---:|:---:|---|:---:|
| 1 | F-S1 | Structural | BLOCKER | CONFIRMED | | — |
| 2 | F-T2 | Test | MAJOR | CONFIRMED | | 1 |
| 3 | F-C1 | Config | MAJOR | CONFIRMED | | — |

## 4. Çelişki Defteri Çözüm Durumu

| # | İddia / Çelişki Konusu | Savunan | Karşı Çıkan | Çözüm Durumu | Adli Çözüm Kanıtı |
|:---:|---|:---:|:---:|:---:|---|
| Ç-01 | | F-S3 | F-A2 | **ÇÖZÜLDÜ** | Test çalıştırıldı ve log kanıtı mühürlendi. |

## 5. Reddedilen Bulgular (Refuted Findings Log)

Verifier tarafından somut karşı-kanıtla çürütülen bulgular (denetim izi için saklanır):

| Bulgu Kimliği | İddia Edilen Kusur | Verifier Karşı Kanıtı |
|:---:|---|---|
| F-L2 | | Belirtilen API metodu 2.0 sürümünde mevcuttur (Context7 kanıtı). |

## 6. İzleme Listesi (Watchlist)

Gürültü filtresine takılan düşük öncelikli / tek kaynaklı hipotezler:

| Bulgu Kimliği | İddia | İzleme Nedeni |
|:---:|---|---|

## 7. Neyi İncelemedik — ZORUNLU

- **Kapsam Dışı Bırakılan Alanlar:** <…>
- **Erişilemeyen Dış Kaynaklar:** <…>
- **`UNVERIFIABLE` Kalan Noktalar:**
  | Bulgu Kimliği | Neden Sınanamadı | Sınanması İçin Ne Gerekir? |
  |:---:|---|---|

## 8. İnceleme ve Ajan İstatistikleri

| Metrik | Tur 1 | Tur 2 | Tur 3 (Derinleşme) | Toplam |
|---|:---:|:---:|:---:|:---:|
| **F-S (Structural)** | | | | |
| **F-L (Literature)** | | | | |
| **F-A (Adversary)** | | | | |
| **F-C (Config)** | | | | |
| **F-T (Test)** | | | | |
| **F-V (Verifier)** | | | | |
| **CONFIRMED** | | | | |
| **REFUTED** | | | | |
| **UNVERIFIABLE** | | | | |
| **≥2 Ajan Desteği (Corroborated)** | | | | |

**Durma Nedeni:** <Standart Tur 2 tamamlandı | Otomatik Deep Tur 3 kritik konuyu kapattı>
