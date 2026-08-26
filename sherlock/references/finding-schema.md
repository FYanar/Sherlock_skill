# Sherlock Bulgu Şeması (Finding Schema 3.0)

Tüm Sherlock uzman alt ajanları ve Lead Hakem bulgularını **birebir** bu formatta yazar. Birleştirme (merge) ve adli tıp doğrulama motoru bu standart alanlara göre deterministik çalışır.

---

## 1. Standart Bulgu Formatı

```markdown
### F-S3
- severity:             MAJOR
- epistemic_confidence: CONFIRMED
- verification_status:  CONFIRMED
- locus:                src/docking/prepare.py:88
- claim:                Metal iyonunun yükü sabit +2 varsayılıyor, ama C3 bunu değişken ilan ediyor.
- evidence:             prepare.py:88 okundu — `charge = 2` sabit atama; 00-case.md C3 ile çelişiyor.
- impact:               Zn dışındaki iyonlarda toplam yük nötrleme bozulur; MD kutusu sessizce yanlış yükle kurulur ve pipeline hata vermeden yanlış sonuç üretir.
- fix:                  Yükü iyon tipine göre `params/metal.dat`'tan oku; sabit atamayı kaldır.
- falsifier:            Cu(+1) ile çalıştırıldığında toplam sistem yükü 0 çıkıyorsa bu bulgu yanlıştır.
- links:                conflicts-with: F-A2, corroborated-by: F-C1
```

---

## 2. Standart Alan Tanımları ve Tipleri

| Alan Adı | Zorunlu | Tip / İzin Verilen Değerler | Kural ve Açıklama |
|---|:---:|---|---|
| `### F-<önek><n>` | ✔ | `F-S` \| `F-L` \| `F-A` \| `F-C` \| `F-T` \| `F-V` \| `F-B` + numara | Benzersiz bulgu kimliği. Numara 1'den başlar, turlar boyunca artarak devam eder (asla yeniden kullanılmaz). |
| `severity` | ✔ | `BLOCKER` \| `MAJOR` \| `MINOR` \| `NIT` | Kusurun ciddiyeti. Şişirme yasaktır. |
| `epistemic_confidence` | ✔ | `CONFIRMED` \| `PLAUSIBLE` \| `SPECULATIVE` | **Araştırmacı Ajanın Güveni:** Doğrudan gözlem (`CONFIRMED`), güçlü çıkarım (`PLAUSIBLE`), şüphe/hipotez (`SPECULATIVE`). |
| `verification_status` | ✔ | `CONFIRMED` \| `REFUTED` \| `UNVERIFIABLE` \| `PENDING_RECHECK` | **Verifier Damgası:** İlk raporlamada `PENDING_RECHECK` yazılır; `sherlock-verifier` incelemesi sonrası damgalanır. |
| `locus` | ✔ | `dosya:satır` \| sembol \| dava iddiası (`C1..Cn`) | Kusurun tam konumu. "Genel olarak" kabul edilmez. |
| `claim` | ✔ | Tek cümle metin | Kusurun net ifadesi (çözüm veya gözlem değil). |
| `evidence` | ✔ | Somut eylem metni | Okunan dosya satırı, çalıştırılan komut, çekilen doküman/literatür URL/PMID/DOI. |
| `impact` | ✔ | Somut etki analizi | Hangi girdide hangi yanlış sonuç veya veri kaybı oluşur. |
| `fix` | ✔ | Minimal düzeltme | En küçük yeterli kod/konfigürasyon değişikliği. |
| `falsifier` | ✔ | Somut yanlışlama testi | Bu bulgunun **yanlış/çürütülmüş** olduğunu kanıtlayacak test veya gözlem. |
| `links` | — | Bağıntı listesi | `depends-on:` \| `conflicts-with:` \| `corroborated-by:` + bulgu kimlikleri. |

---

## 3. Ajan Kimlik Önekleri ve Sorumluluk Matrisi

| Önek | Uzman Ajan Kimliği | Uzmanlık ve Üretilen Bulgu Türü |
|:---:|---|---|
| **`F-S`** | `sherlock-structural` | Kod mimarisi, AST, gereksiz karmaşıklık, dev fonksiyonlar, duplikasyon ve veri akışı kusurları. |
| **`F-L`** | `sherlock-literature` | Biyofiziksel/kimyasal normlar, kütüphane sözleşmeleri, API/CLI standartları ve literatür çelişkileri. |
| **`F-A`** | `sherlock-adversary` | Pre-mortem, arıza rotaları, sınır durum regresyonları ve çökme tuzakları. |
| **`F-C`** | `sherlock-config` | SSOT, tolerans çatışmaları, konfigürasyon sapmaları ve ölü parametreler (`dead keys`). |
| **`F-T`** | `sherlock-test` | Test süiti açıkları, mock kirliliği ve kağıt-kaplan testler (`FAIL-PAPER-TIGER-TEST`). |
| **`F-V`** | `sherlock-verifier` | Ham disk çıktısı, log veya SHA-256 hash bütünlüğü bozukluğu gibi doğrudan adli doğrulamada yakalanan kusurlar. |
| **`F-B`** | Lead Hakem (Patron) | Hakemin kendi bağımsız okumasından çıkardığı, açıkça etiketlenmiş patron bulgusu. |

---

## 4. Şiddet (Severity) Kriterleri

- **`BLOCKER`:** Bu haliyle devam edilirse sistem çöker, sessizce yanlış sonuç üretir, veri kaybolur veya anayasa delinir. Kapatılmadan kesinlikle `GO` verilemez.
- **`MAJOR`:** Ciddi teknik/mantıksal kusur; belirli ve gerçekçi senaryolarda başarısızlığa yol açar. Ölçülebilir koşullarla `GO-WITH-CONDITIONS`'a konu olabilir.
- **`MINOR`:** Sınırlı etkili kusur; düzeltilmesi gerekir ancak nihai kararı engellemez.
- **`NIT`:** Küçük tutarsızlık, stil veya dokümantasyon eksiği. Eylem planını tıkamaz, ekte listelenir.

---

## 5. Epistemic Confidence vs. Verification Status Ayrımı

Sistemde araştırmacının iddiası ile adli doğrulayıcının damgası **kesinlikle iki ayrı alanda tutulur**:
1. **`epistemic_confidence` (Araştırmacı):**
   * `CONFIRMED`: Ajan bizzat gözlemledi (kodu okudu, test çalıştırdı, Context7/PMID çekti).
   * `PLAUSIBLE`: Güçlü mantıksal çıkarım, ancak dolaylı kanıt.
   * `SPECULATIVE`: Şüphe veya uç senaryo hipotezi.
2. **`verification_status` (Doğrulayıcı):**
   * `CONFIRMED`: Verifier ham diski, komut çıktısını ve hash'i doğruladı.
   * `REFUTED`: Verifier iddianın yanlış olduğunu somut karşı-kanıtla ispatladı.
   * `UNVERIFIABLE`: Mevcut disk logları veya ortam araçlarıyla bağımsız doğrulanamadı.
   * `PENDING_RECHECK`: Tur 2 veya Tur 3'te tekrar denetlenecek.
