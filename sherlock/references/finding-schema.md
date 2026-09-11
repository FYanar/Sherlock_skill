# Sherlock Bulgu Şeması (Finding Schema 4.0)

Tüm Sherlock uzman alt ajanları ve Lead Hakem bulgularını **birebir** bu formatta yazar.

---

## 1. Standart Bulgu Formatı

```markdown
### F-C3
- severity:             MAJOR
- epistemic_confidence: CONFIRMED
- verification_status:  PENDING_RECHECK
- locus:                src/docking/prepare.py:88
- claim:                Metal iyonunun yükü sabit +2 varsayılıyor, ama C3 bunu değişken ilan ediyor.
- evidence:             prepare.py:88 okundu — `charge = 2` sabit atama; 00-case.md C3 ile çelişiyor.
- impact:               Zn dışındaki iyonlarda toplam yük nötrleme bozulur.
- fix:                  Yükü iyon tipine göre `params/metal.dat`'tan oku; sabit atamayı kaldır.
- falsifier:            Cu(+1) ile çalıştırıldığında toplam sistem yükü 0 çıkıyorsa bu bulgu yanlıştır.
- links:                conflicts-with: F-A2, corroborated-by: F-R1
```

---

## 2. Alan Tanımları

| Alan | Zorunlu | İzin Verilen Değerler | Kural |
|---|:---:|---|---|
| `### F-<önek><n>` | ✔ | `F-C` \| `F-A` \| `F-R` \| `F-B` + numara | Benzersiz bulgu kimliği. |
| `severity` | ✔ | `BLOCKER` \| `MAJOR` \| `MINOR` \| `NIT` | Şişirme yasaktır. |
| `epistemic_confidence` | ✔ | `CONFIRMED` \| `PLAUSIBLE` \| `SPECULATIVE` | Araştırmacının güveni. |
| `verification_status` | ✔ | `CONFIRMED` \| `REFUTED` \| `UNVERIFIABLE` \| `PENDING_RECHECK` | Research & Verify damgası. |
| `locus` | ✔ | `dosya:satır` \| sembol \| `C1..Cn` | Tam konum. |
| `claim` | ✔ | Tek cümle | Kusurun net ifadesi. |
| `evidence` | ✔ | Somut eylem | Okunan satır, çalıştırılan komut, URL/DOI. |
| `impact` | ✔ | Somut etki | Hangi girdide hangi yanlış sonuç. |
| `fix` | ✔ | Minimal düzeltme | En küçük yeterli değişiklik. |
| `falsifier` | ✔ | Somut test | Bulguyu çürütecek gözlem. |
| `links` | — | Bağıntı listesi | `depends-on:` \| `conflicts-with:` \| `corroborated-by:` |

---

## 3. Ajan Önekleri

| Önek | Ajan | Uzmanlık |
|:---:|---|---|
| **`F-C`** | Code Analyst | Mimari, AST, SSOT, konfigürasyon, dead code, test kalitesi. |
| **`F-A`** | Adversary | Pre-mortem, arıza rotaları, sınır durum regresyonları. |
| **`F-R`** | Research & Verify | Literatür, standartlar, kanıt doğrulama ve Bayesçi damgalama. |
| **`F-B`** | Lead Hakem | Hakemin bağımsız patron bulgusu. |

---

## 4. Şiddet Kriterleri

- **`BLOCKER`:** Sistem çöker, sessizce yanlış sonuç üretir veya anayasa delinir. `GO` verilemez.
- **`MAJOR`:** Ciddi kusur; gerçekçi senaryolarda başarısızlığa yol açar. `GO-WITH-CONDITIONS` olabilir.
- **`MINOR`:** Sınırlı etki; düzeltilmeli ama kararı engellemez.
- **`NIT`:** Stil/dokümantasyon eksiği. Ekte listelenir.

---

## 5. Epistemic Confidence vs. Verification Status

- **`epistemic_confidence` (Araştırmacı):** `CONFIRMED` (bizzat gözlem), `PLAUSIBLE` (güçlü çıkarım), `SPECULATIVE` (hipotez).
- **`verification_status` (Doğrulayıcı):** `CONFIRMED` (ham disk doğrulandı), `REFUTED` (somut karşı-kanıt), `UNVERIFIABLE` (sınanamadı), `PENDING_RECHECK`.
