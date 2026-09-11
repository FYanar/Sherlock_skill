# Sherlock Birleştirme Kuralları (Merge & Adjudication Engine 4.0)

Bu dosya Lead Hakem Heyetine aittir. 3 uzman ajandan gelen raporları deterministik biçimde `findings.md` ve `40-verdict.md`'ye indirger.

---

## 1. Algoritmik Birleştirme Adımları

### Adım 1 — Topla ve İndeksle
3 rapordan (`10-r1-code-analyst.md`, `10-r1-adversary.md`, `10-r1-research-verify.md`) tüm bulguları `findings.md`'ye aktar.
- Research & Verify'ın doğrulama damgasını `verification_status` alanına işle.
- Araştırmacının `epistemic_confidence` değerini koru.

### Adım 2 — Deduplikasyon
Aynı `(locus, claim)` çiftine işaret eden bulgular tek bir kanonik bulguda birleşir:
- **Kimlik:** En düşük numaralı kimlik korunur; diğerleri `corroborated-by:` listesine.
- **Şiddet:** En yüksek atanır.
- **Kanıt:** Tüm kanıtlar birleştirilir.
- **Fix:** En minimal düzeltme seçilir.

### Adım 3 — Çoklu Ajan Destek Yükseltmesi (Corroboration Escalation)
Aynı kusuru **≥2 bağımsız ajan** (`F-C`, `F-A`, `F-R`) tespit ettiyse:
- Şiddet bir kademe artırılır: `NIT → MINOR → MAJOR → BLOCKER` (tavan: BLOCKER).
- **Doğruluk Koşulu:** Yükseltme yalnızca `verification_status ∈ {CONFIRMED, PENDING_RECHECK}` olan bulgular için geçerlidir. `REFUTED` veya `UNVERIFIABLE` (spekülatif/kanıtsız) bulgular asla yükseltilmez; doğrudan Adım 4 veya Adım 5'e sevk edilir.
- Patron bulgusu (`F-B`) bağımsız destek sayılmaz.

### Adım 4 — REFUTED İşleme
- `REFUTED` bulgular eylem planından çıkarılır.
- `40-verdict.md` "Reddedilen Bulgular" tablosuna gerekçesiyle kaydedilir.
- `REFUTED` bulguya bağımlı olanlar yeniden değerlendirilir.

### Adım 5 — Gürültü Filtresi (Watchlist)
Şu 3 koşulu birlikte sağlayanlar İzleme Listesine aktarılır:
1. `SPECULATIVE` veya `UNVERIFIABLE`, ve
2. Tek ajan tarafından raporlandı, ve
3. `falsifier` boş veya sınanamaz.

### Adım 6 — Çelişki Defteri
İki ajan çelişiyorsa hakem taraf tutmaz; Çelişki Defterine kaydeder:
| # | İddia | Savunan | Karşı Çıkan | Çözüm İçin Kanıt | Hakem Ataması |
|---|---|---|---|---|---|

### Adım 7 — Patron Bulguları (F-B)
Lead Hakemin kendi bağımsız bulgusu. Standart şemaya uyar, bağımsız oy sayılmaz.

---

## 2. Önceliklendirme Matrisi

Bulgular `Severity × Verification_Status` formülüyle sıralanır:

| Severity \ Verification | CONFIRMED | PENDING_RECHECK | UNVERIFIABLE | REFUTED |
|---|:---:|:---:|:---:|:---:|
| **BLOCKER** | **1 (Acil)** | **2** | **4** | → Kapat |
| **MAJOR** | **3** | **5** | **7** | → Kapat |
| **MINOR** | **6** | **8** | **9** | → Kapat |
| **NIT** | Ek Liste | Ek Liste | Ek Liste | → Kapat |

Bağımlılık sıralaması: `depends-on` öncülü her zaman üst sırada.

---

## 3. Eylem Planı ve Koşullu JIT Çözüm Motoru (`20-plan.md`)

Lead Architect doğrulanmış bulgulardan tedavi planını (`20-plan.md`) türetirken şu kurallara uyar:

1. **Katı Teşhis/Tedavi Ayrımı:** Aşama 2 (adli tıp taraması) sırasında alt ajanların `brainstorming` veya `find-skills` çalıştırması delilden kopmayı engellemek için kesinlikle yasaktır.
2. **JIT Brainstorming (Mimari Çözüm Tartımı):** Yalnızca `CONFIRMED BLOCKER` veya yapısal `MAJOR` mimari kusurlarında (God Node, monolitik ayrışma, deadlock riski) devreye girer. Lead Architect en az 2 alternatif onarım rotasını, artı/eksi (trade-off) analizini `20-plan.md` içine dahil ederek en temiz çözümü seçer.
3. **JIT Find-Skills (Domain Yeteneği Bağlama):** Bulunan kusurun çözümü özel bir alan uzmanlığı gerektiriyorsa (örn. veri dönüştürme `data-transform`, ileri güvenlik sertifikasyonu `security-and-hardening`, dokümantasyon `doc-generator`), Lead Architect `find-skills` ile uygun yerel yeteneği keşfeder ve eylem planındaki ilgili iş paketine (`WP-<n>`) doğrudan yürütücü rehber olarak atar.

---

## 4. Çok Turlu İlerleme

- **Tur 1:** 3 ajan geniş tarama. Lead merge → findings.md.
- **Yükseltme koşulu:** Açık BLOCKER / çözülememiş çelişki / kritik UNVERIFIABLE → Tur 2 açılır.
- **Tur 2:** Odaklı çapraz sorgu (yalnızca atanmış açık soruya odaklanır).
- **Tur 3:** Yalnızca Tur 2'de çözülemeyenler için nihai karar.

---

## 5. Nihai Karar Tablosu

| Karar | Koşul |
|---|---|
| **`GO`** | Açık BLOCKER yok, doğrulanmış MAJOR yok. |
| **`GO-WITH-CONDITIONS`** | BLOCKER yok; MAJOR'lar ölçülebilir koşullarla kapatılabiliyor. |
| **`NO-GO`** | CONFIRMED BLOCKER var, koşulla kapatılamıyor. |
| **`INSUFFICIENT-EVIDENCE`** | Kritik soru UNVERIFIABLE kaldı. |

`40-verdict.md`'de "Neyi İncelemedik" ve "Taviz Verilmeyen Riskler" bölümleri zorunludur.
