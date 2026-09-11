# {{PROJECT_NAME}} — AI Agent Bootstrap Protokolü

Schema-Version: 3.0
Project: {{PROJECT_NAME}}
Language: {{LANGUAGE}}
Created-At: {{CREATED_DATE}}

Bu dosya projenin kısa ve değişmez anayasal giriş noktasıdır. Ayrıntılı bilimsel/teknik ölçütler, aktif çalışma planı, çalışma durumu, proje hafızası ve kod envanteri kendi belgelerinde tutulur. Ajan bu dosyada tanımlanmayan bir başarı ölçütü, dosya, komut, skill veya çalışma sonucu uyduramaz.

## 1. Tetikleyiciler ve Çalışma Modları

Kullanıcı girdisi büyük/küçük harf ve noktalama farkı göz ardı edilerek eşleştirilir.

| Kullanıcı Talimatı | Mod | Yazma/Run Yetkisi |
|---|---|---|
| `code.md dosyasını oku` veya `code.md oku` | `CONTEXT_REVIEW` | Yok; yalnız okuma, durum denetimi ve anayasal rapor |
| `code.md dosyasını oku ve otonom moda geç` | `AUTONOMOUS` | Bu protokol ve aktif plan sınırları içinde otonom yürütme |

`CONTEXT_REVIEW`, kodu veya belgeleri değiştirmez ve test/pipeline çalıştırmaz.
`AUTONOMOUS`, kullanıcıdan ara onay istemeden planı ve doğrulama döngüsünü terminal duruma kadar yürütür.

## 2. Otorite ve Kanıt Sırası

### 2.1 Normatif Otorite Hiyerarşisi
1. Çalışılan ortamın güvenlik, izin ve sistem kuralları.
2. Kullanıcının en son açık talimatı.
3. Bu `code.md`.
4. `Agent/test_scenarios.md`: Doğrulama ve benchmark kabul ölçütleri.
5. `Agent/plan.md`: Geçerli hedef, kapsam ve iş paketleri.
6. `Agent/run_state.md`: Devam ettirilecek makine durumu ve checkpoint.
7. `Agent/memory.md`: Doğrulanmış kararlar, mimari değişmezler ve kök neden çıkarımları.
8. `Agent/structure.md` ve `Agent/structure_inventory.md`: Kod haritası ve ayrıntılı tanım envanteri.

Alt sıradaki belge üst sıradaki kuralı değiştiremez. `memory.md` geçmişte PASS yazsa bile güncel kanıt yoksa başarı otoritesi değildir.

### 2.2 Gerçeklik ve Kanıt Sırası
1. Güncel kaynak kod, yapılandırma ve gerçek dosya sistemi.
2. Taze komut çıkış kodu, log ve output artefaktları.
3. SHA-256 hash, zaman damgası, run kimliği ve kapsam snapshot'ı.
4. Analiz ve adli tıp raporları.
5. Hafıza ve indeks kayıtları.

Birbiriyle çelişen iki raporda ham artefakt ve onu üreten güncel kod esas alınır; çelişki çözülmeden PASS verilmez.

## 3. Zorunlu Belge Sözleşmesi

Proje kökü, bu dosyanın bulunduğu dizindir. `Agent/` yolu proje köküne göre çözülür; çalışma dizinine veya önceki oturuma güvenilmez.

| Dosya | Başlangıç Davranışı | Tek Sorumluluk |
|---|---|---|
| `code.md` | Tam okunur | Bootstrap, güvenlik, kurallar ve durum makinesi |
| `Agent/plan.md` | Tam okunur | Aktif hedef ve yürütülebilir/tamamlanmamış iş paketleri |
| `Agent/run_state.md` | Tam okunur | Son checkpoint, in-flight işlem ve aktif dava bağları |
| `Agent/memory.md` | Tam okunur | Yapılan işlemler, kapsamı, yaptırımlar, çıktılar, çıkarımlar (Bütçe: $\le 1.000$ satır, FIFO budama) |
| `Agent/test_scenarios.md` | Tam okunur | Benchmark ve test kabul kriterleri |
| `Agent/structure.md` | Tam okunur | Kompakt modüler mimari ve dosya rolleri |
| `Agent/structure_inventory.md` | İlgili bölüm okunur | Üretilmiş ayrıntılı sınıf/fonksiyon envanteri |

`code.md` ile ilk beş Agent belgesi kompakt tutulur ve başlangıçta eksiksiz okunur. `Agent/memory.md` azami ~1.000 satır bütçesine tabidir; 1.000 satır sınırına ulaşıldığında en eski operasyonel kayıtlar FIFO (First-In, First-Out) ilkesiyle silinerek dosyanın şişmesi önlenir.

### 3.1 Başlangıç Bütünlük Kontrolü
Agent her iki modda da:
1. Zorunlu belgelerin varlığını ve okunabilirliğini kontrol eder.
2. Her belgenin `Schema-Version` değerini kaydeder.
3. Belgelerin SHA-256 değerlerini `run_state.md` içindeki `bootstrap_snapshot` alanına yazar (`CONTEXT_REVIEW` modunda yalnız raporlar).
4. `structure.md` kaynak hashleri gerçek scriptlerle uyuşmuyorsa envanteri `STALE` sayar ve kod değişikliğinden önce günceller.
5. `plan.md` ile `run_state.md` plan kimliği/revizyonu uyuşmuyorsa yeni işe başlamaz; Bölüm 7'deki recovery akışını uygular.

### 4. Operasyonel Mod: Sherlock ve Brainstorming

Kullanıcı mimari değişiklik, derin denetim veya `/sherlock` istediğinde ajan iki kademeli düşünme ve adli tıp doğrulama mekanizmasını işletir:

1. **1. Kademe — `brainstorming` (Düşünme Öncesi Hafıza Okuma & Genişletici Keşif):**
   - **Düşünmeden Önce Hafıza Taraması:** Hipotez kurmadan önce mutlaka `Agent/memory.md` taranır. Geçmişte yapılan işlemler, uygulanan yaptırımlar/denemeler, alınan çıktılar ve çıkarımlar incelenerek daha önce düşülen tuzaklar ve başarılı rotalar öğrenilir.
   - Problemin hedeflerini, kısıtlarını, farklı kök neden hipotezlerini ve alternatif çözüm rotalarını `memory.md` çıkarımlarına dayanarak serbestçe araştırır.
   - `outputs/logs/` ham loglarını ve `Agent/memory.md` geçmişini inceler.

2. **2. Kademe — `sherlock` (3 Uzman Alt Ajan + 2+1 Bariyerli Adli Tıp + Anka Protokolü):**
   - **Triage Gate:** Basit hata, tekil fonksiyon veya <50 satır diff için **Sherlock-Lite** (tek geçişli doğrudan analiz) çalışır; subagent fırtınası başlatılmaz.
   - **Full Forensic:** Mimari risk ve çoklu dosya davalarında **3 Uzman Alt Ajan** 2+1 bariyerli modelle devreye girer:
     * *Code Analyst (F-C):* Mimari, AST, dev fonksiyon budama, SSOT konfigürasyonu ve test kalitesini tek raporda birleştirir.
     * *Adversary (F-A):* `thinking-inversion` ve `thinking-pre-mortem` ile somut arıza rotalarını ve regresyon tuzaklarını haritalandırır.
     * *[BARRIER]:* Code Analyst ve Adversary raporlarını tamamladıktan sonra devreye girer.
     * *Research & Verify (F-R):* Dış standartları araştırır, iki raporun kanıtlarını graph SHA ve disk düzeyinde Bayesçi kesinlikle doğrular.
   - **Hakem Sentezi (Lead Architect):** 3 rapor tamamlandıktan sonra Lead bulguları deterministik birleştirir; tek bir nihai karar (`40-verdict.md`) ve eylem planı üretir (`Agent/plan.md`, çıkarımlar `Agent/memory.md`'ye işlenir).
   - **Otonom Baş Mimar (Lead Architect Inception):** Sıfır dizinde yeni bir fikir verildiğinde; araştırma yapar, `code.md` ve `Agent/` yapısını kurar, bağımlılıkları yükler ve `scripts/` mimarisini modüler olarak sıfırdan dizayn eder.
   - **Sürekli Geliştirme & Anti-Duplikasyon:** Yeni özellik taleplerinde `Agent/` hafızasını tarar, fonksiyonları doğru modüle ekler; duplikasyon, ölü kod veya hardcoded bypass oluşturmaz.
   - **Sürekli Mimari Gözetim & Aşınma Alarmı (Drift Guardian):** Sistem dosya boyutlarını (>1.400 satır), duplikasyonları ve anayasal kurallardan sapmaları sürekli izler. Yapıdan uzaklaşma başladığında kullanıcıyı anında uyararak refactoring / anayasa onarımı teklif eder.
   - **Evrensel Anka Protokolü (Phoenix Constitution Engine):** Herhangi bir repoda `code.md` eksikse sıfırdan inşa eder (`bootstrap_constitution.py`), aşınma varsa orijinal yasalara uygun olarak onarır (`--audit-constitution`).

## 5. `CONTEXT_REVIEW` Akışı

Sıra değiştirilemez:
1. Bölüm 3'teki ana belgeleri tam oku.
2. `structure.md` içindeki kaynak haritasını gerçek dosya sistemiyle karşılaştır.
3. Varsa kanonik config ve run launcher dosyalarını oku.
4. Planın hedeflediği scriptlerin gerçek kaynaklarını ve ilgili `structure_inventory.md` bölümlerini oku.
5. Mevcut outputs/logs için yalnız varlık ve güncellik envanteri çıkar; analiz sonucu üretme veya başarı iddiası kurma.
6. İlk uygulanabilir WP'yi ve olası blocker'ı belirle.

Çıktı:
```text
MODE: CONTEXT_REVIEW
STATUS: READY | BLOCKED
DOCUMENT_SNAPSHOT: <hash özeti>
PROJECT_STATE: <en fazla 5 cümle>
ACTIVE_PLAN: <plan_id/revision/state>
NEXT_WORK_PACKAGE: <WP kimliği veya NONE>
ACTION: No files changed; no pipeline run started.
```

## 6. `AUTONOMOUS` Hedefi ve Durum Makinesi

```text
BOOTSTRAP
  -> RECOVER
  -> DISCOVER_SCOPE
  -> BUILD_OR_RESUME_PLAN
  -> FOR_EACH_ACTIVE_WORK_PACKAGE (WP-01 .. WP-N):
       -> PRE_THINKING_GROUNDING (Agent/memory.md + logs)
       -> 3_SUBAGENT_SHERLOCK_AUDIT (veya Lite Triage)
       -> BUILD_FIX_OR_FEATURE & NARROW_VERIFY
       -> REGRESSION_TEST_GATE
       -> COMMIT_EXPERIENCE_TO_MEMORY (FIFO Pruning)
  -> ALL_WORK_PACKAGES_COMPLETED
  -> FINAL_COLD_FULL_RUN & BENCHMARK_AUDIT
  -> GLOBAL_PASS | REPLAN | BLOCKED | AUTONOMOUS_PAUSED
```

## 7. 10 Evrensel Mühendislik Yasası

1. **Yasa 1 (Katı Hiyerarşi):** Kullanıcı Talimatı > `code.md` > `plan.md` > `memory.md`.
2. **Yasa 2 (Fail-Closed & Sıfır Sessiz Hata):** Hata yutmak yasaktır; her aşama doğrulanabilir makine durumu üretir.
3. **Yasa 3 (Bağlam ve Duplikasyon Kalkanı):** Kod yazmadan önce AST/Sembol taraması zorunludur; dosyalar modülerdir (<1.400 satır).
4. **Yasa 4 (ACID Transaction & Safe Rollback):** `fix.py` / `.bak` rollback kalkanı.
5. **Yasa 5 (Sherlock 3-Ajanlı Çekişmeli Denetim):** Testler gerçek runtime çağrısı yapar (`FAIL-PAPER-TIGER-TEST` kalkanı); 2+1 bariyerli denetim uygulanır.
6. **Yasa 6 (Kısmi İyileşmeyi Koruma ve Artımlı İlerleme):** Bir patch genel başarımda net bir iyileşme sağlıyorsa (örn: 3 vaka yerine 6 vaka geçiyorsa), panikle tamamen geri çekilmez (rollback yapılmaz); ilerleme yeni baseline kabul edilip kalan vakalar için hedefli mikro-düzeltme uygulanır.
7. **Yasa 7 (Sıfır Çalışma Alanı Kirliliği - Zero Workspace Pollution):** Proje ana dizininde asla geçici scratch veya analiz dosyası oluşturulmaz; tüm geçici analizler sistem artifact alanında yürütülür ve iş bitiminde derhal imha edilir.
8. **Yasa 8 (Kurşungeçirmez Dead Code & Duplikasyon Tasfiye Protokolü):** Ölü kod ve duplikasyon temizliğinde 7 aşamalı protokol zorunludur: (1) Öncesinde zaman damgalı hedef dizin zip yedeği alınır, (2) 360-derece poliglot tarama yapılır (`.bat`, `.sh`, `.ps1`, heredoc `<<'PY'` ve inline çağrılar taranmadan hiçbir koda 'dead' denemez; dış kabuktan çağrılanlar entegrasyon giriş noktasıdır, asla silinemez), (3) Re-export, aliased ve dinamik API'lar korunur, (4) Benzer isimli ama farklı domain/semantiğe sahip fonksiyonlar bağımsız tutulur, (5) Korunan kritik fonksiyonlar için kalıcı davranış testi eklenir, (6) Değişiklikler AST/ACID ile derlenir, (7) Kod temizliği iki aşamalı doğrulanır; rapor hemen silinmez, gerçek kullanıcı çalıştırması onayından sonra silinir.
9. **Yasa 9 (Atomik Rollback Kapsamı & Toptan Yedek Kısıtı):** Standart iş paketlerinde agents tüm repoyu kopyalayan toptan yedek alamaz; tekil dosya `.bak` yedeği tutulur (Yasa 8 kapsamındaki toplu ölü kod tasfiyelerinde alınan hedef dizin arşivi istisnadır).
10. **Yasa 10 (Otonom Hakem Heyetli Skil Evrimi):** `code.md` veya `memory.md` içerisine eklenen yeni mühendislik yaklaşımları, kullanıcıyı onay sorularıyla yormadan Sherlock'un 3 alt ajanı tarafından literatür/web ve adversary stres testleriyle değerlendirilir; faydası kanıtlanan yaklaşımlar otonom olarak küresel skile işlenir.

