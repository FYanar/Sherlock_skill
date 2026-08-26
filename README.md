# 🕵️ Sherlock

<p align="center">

### **Autonomous Multi-Agent Software Forensics**

**Kodunu sadece incelemez. Sorgular, karşılaştırır, doğrular ve kanıtlar.**

</p>

---

## 🧠 Sherlock Nedir?

Sherlock, büyük ve karmaşık yazılım projelerini **tek bir AI ajanının görüşüne bırakmak yerine**, farklı uzmanlıklara sahip bağımsız ajanlarla inceleyen otonom bir repository analiz sistemidir.

Amaç yalnızca bug bulmak değildir.

Sherlock şu soruya cevap vermeye çalışır:

> **“Bu proje gerçekten iddia ettiği şeyi doğru, tutarlı ve güvenilir biçimde yapıyor mu?”**

```text
                    REPOSITORY
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   STRUCTURE        ADVERSARIAL       LITERATURE
        │               │               │
        └───────┬───────┴───────┬───────┘
                ▼               ▼
              CONFIG           TEST
                └───────┬───────┘
                        ▼
                   🔬 VERIFIER
                        │
                        ▼
                  ⚖️ VERDICT
```

---

# ✨ Neden Sherlock?

Klasik AI code review çoğu zaman şunu yapar:

```text
Dosyayı oku
   ↓
Şüpheli kodu bul
   ↓
Yorum yap
```

Sherlock ise problemi **sistem seviyesinde** ele alır:

```text
Kod
 │
 ├── Configuration
 ├── Runtime flow
 ├── Tests
 ├── Documentation
 ├── External evidence
 └── Agent findings
          │
          ▼
      CROSS-CHECK
          │
          ▼
       VERDICT
```

Çünkü gerçek hatalar çoğu zaman tek bir satırda değildir.

Örneğin:

```text
CLI parametresi doğru
        ↓
Config dosyası doğru
        ↓
Fonksiyon doğru
        ↓
AMA
        ↓
runtime sırasında başka default değer kullanılıyor.
```

Her parçaya ayrı ayrı bakıldığında sistem doğru görünebilir.

Sherlock bu parçaları **birbirine karşı doğrular**.

---

# 🤖 6 Uzman Ajan

Sherlock farklı bakış açılarını bilinçli olarak ayırır.

| Ajan               | Görevi                                                           |
| ------------------ | ---------------------------------------------------------------- |
| 🧱 **Structural**  | Mimari, call-flow, dead code, duplicate logic                    |
| 📚 **Literature**  | Teknik iddiaları literatür ve resmi kaynaklarla karşılaştırır    |
| 🧨 **Adversarial** | Sistemi kırmaya çalışır, gizli varsayımları arar                 |
| ⚙️ **Config**      | Parametrelerin gerçek runtime akışını izler                      |
| 🧪 **Test**        | Testlerin gerçekten davranışı doğrulayıp doğrulamadığını inceler |
| 🔬 **Verifier**    | Diğer ajanların bulgularını bağımsız olarak doğrular             |

Önemli fark:

> **Sherlock ajanların birbirine inanmasını istemez. Birbirlerini kanıtlamalarını ister.**

---

# 🔎 Sherlock Neleri Bulabilir?

Sherlock özellikle klasik code review araçlarının kaçırabileceği problemleri hedefler:

* duplicated business logic
* dead / unreachable code
* yanlış runtime parameter propagation
* config override hataları
* hidden fallback davranışları
* dokümantasyon ↔ kod çelişkileri
* mock ağırlıklı sahte güven veren testler
* yanlış veya eksik scientific assumptions
* birbirini çürüten farklı implementasyonlar
* Single Source of Truth ihlalleri
* pipeline boyunca sessizce bozulan veri veya state

---

# 🧪 Test Geçiyor Diye Kod Doğru Değildir

Sherlock özellikle **Paper-Tiger Tests** dediğimiz testleri araştırır.

Örneğin:

```python
assert "timeout" in source_code
```

testi geçebilir.

Ama gerçek soru şudur:

```text
CLI --timeout 60
        ↓
runtime gerçekten 60 kullanıyor mu?
```

Sherlock testin varlığını değil, **kanıt gücünü** değerlendirir.

---

# ⚖️ Kanıta Dayalı Karar

Her bulgu yalnızca “AI böyle düşünüyor” şeklinde bırakılmaz.

```text
FINDING
   ↓
SOURCE EVIDENCE
   ↓
CROSS-AGENT CHECK
   ↓
VERIFICATION
   ↓
SEVERITY
   ↓
FINAL VERDICT
```

Sonuçlar örneğin şöyle sınıflandırılabilir:

```text
🔴 BLOCKER
🟠 CRITICAL
🟡 MAJOR
🔵 MODERATE
⚪ MINOR
```

Ayrıca Sherlock **confidence** ile **verification** kavramlarını birbirinden ayırır.

Bir ajan çok emin olabilir.

Bu, onun haklı olduğu anlamına gelmez.

---

# 🧠 Repository Intelligence

Sherlock yalnızca tek seferlik analiz yapan bir prompt değildir.

Repository için yerel bir bilgi katmanı oluşturabilir ve önceki incelemelerden yararlanabilir.

```text
SOURCE CODE
    │
    ├── Architecture
    ├── Config
    ├── Tests
    ├── Previous Findings
    └── Project Rules
            │
            ▼
      KNOWLEDGE BASE
            │
            ▼
       NEXT ANALYSIS
```

Ancak temel prensip değişmez:

> **Mevcut repository her zaman hafızadan daha üst otoritedir.**

---

# 🔥 Neden Kullanmalısınız?

Sherlock özellikle şu durumlarda faydalıdır:

### Büyük AI-generated codebase'ler

AI ajanları hızlı kod üretir.

Aynı hızla duplicate logic, eski fallback ve çelişkili implementasyon da üretebilir.

Sherlock bunları repository seviyesinde arar.

### Bilimsel yazılımlar

Bioinformatics, computational biology, docking, ML ve quantitative pipeline'larda kodun çalışması yeterli değildir.

**Bilimsel olarak da doğru olması gerekir.**

### Uzun süre geliştirilmiş projeler

Bir proje büyüdükçe:

```text
eski kod
+
yeni kod
+
fallback
+
config
+
tests
+
documentation
```

birbirinden kopmaya başlayabilir.

Sherlock tam olarak bu kopmaları araştırır.

### Kritik release öncesi

Bir repository'yi publication, production veya büyük refactor öncesi bağımsız şekilde sorgulamak için kullanılabilir.

---

# 🚀 Kullanım

Codex üzerinde:

```text
$sherlock Audit this repository end-to-end.
```

Belirli bir alan için:

```text
$sherlock Investigate runtime configuration flow.
```

Bir iddiayı doğrulamak için:

```text
$sherlock Verify whether the implementation really matches the documented behavior.
```

---

# 🕵️ Sherlock Felsefesi

```text
TRUST NOTHING.

TRACE EVERYTHING.

CHALLENGE ASSUMPTIONS.

VERIFY CLAIMS.

PRESERVE EVIDENCE.
```

<p align="center">

### Bir kod review aracı değil.

## **Repository Investigation Engine.**

**Investigate → Challenge → Verify → Verdict**

</p>
