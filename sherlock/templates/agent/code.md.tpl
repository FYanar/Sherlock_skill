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
6. Ortamda tanımlanan bilgi tabanı MCP sunucusunun erişilebilirliğini doğrular. Doğrudan erişilemiyorsa veya dosyalar silinmişse Sherlock yerleşik şablonuyla (`bootstrap_knowledge_base.py`) `Agent/knowledge_base/`, `tools/run_mcp.py` ve `.mcp.json` altyapısını otomatik restore eder; kullanıcıya oturumu yeniden başlatma uyarısını raporlar; yerel arama (`grep_search`) ve dosya tarama araçlarıyla kesintisiz çalışmayı sürdürür, gereksiz `BLOCKED` durumuna girmez.

## 4. Varsayılan Operasyonel Mod: Sherlock ve Brainstorming Zorunluluğu

Kullanıcının her mesajında `/sherlock` yazmasına gerek yoktur. Ajan bu protokolü okuduğu andan itibaren **Sherlock 6-Ajanlı Çekişmeli Adli Tıp Protokolünü ve Brainstorming aşamasını varsayılan operasyonel modu** olarak kabul eder.

Yeni plan yazılırken, mimari kararlar alınırken, refactoring yapılırken veya bir test/analiz yürütülürken ajan körlemesine kod değiştiremez; zorunlu olarak iki kademeli düşünme ve adli tıp doğrulama mekanizmasını işletir:

1. **1. Kademe — `brainstorming` (Düşünme Öncesi Hafıza Okuma & Genişletici Keşif):**
   - **Düşünmeden Önce Hafıza Taraması:** Hipotez kurmadan önce mutlaka `Agent/memory.md` taranır. Geçmişte yapılan işlemler, uygulanan yaptırımlar/denemeler, alınan çıktılar ve çıkarımlar incelenerek daha önce düşülen tuzaklar ve başarılı rotalar öğrenilir.
   - Problemin hedeflerini, kısıtlarını, farklı kök neden hipotezlerini ve alternatif çözüm rotalarını `memory.md` çıkarımlarına dayanarak serbestçe araştırır.
   - `outputs/logs/` ham loglarını ve `Agent/memory.md` geçmişini inceler.

2. **2. Kademe — `sherlock` (Skill-Infused Deep Mode: 6 Uzman Alt Ajan + 1 Hakem Sentezi + Anka Protokolü):**
   - `brainstorming` aşamasında not edilen bilgileri, `Agent/memory.md` öğrenimlerini ve ham kanıtları temel alır.
   - **6 Uzman Alt Ajan (Özel Skillerle Donatılmış Olarak)** `code.md` ve `Agent/memory.md` bağlamını yükleyerek paralel devreye girer:
     * *Structural & AST Auditor:* `code-simplification` + `thinking-systems` ile mimari, AST, dev fonksiyon budama ve sistemik etki matrisini denetler.
     * *Literature & Domain Auditor:* `source-driven-development` + `search_web` + Context7 ile standartlar, kütüphane sözleşmeleri ve best practice'leri inceler.
     * *Adversary & Risk Auditor:* `thinking-inversion` + `thinking-pre-mortem` ile "Sistem nasıl çöker?" analizi ve arıza rotalarını çıkarır.
     * *Evidence & Artifact Verifier:* `thinking-bayesian` + `goal-verifier` ile ham disk loglarını, hashleri ve koordinatları Bayesçi kesinlikle doğrular.
     * *Config, SSOT & Boundary Auditor:* `thinking-triz` + `thinking-systems` ile SSOT yapılandırması ve tolerans çatışmalarını çözer.
     * *Anti-Paper-Tiger & Test Auditor:* `test-driven-development` + `debugging-and-error-recovery` ile test süitini, gerçek çağrıları ve regresyon kalkanını denetler.
   - **Hakem Sentezi (Lead + Verifier):** 5 araştırmacı tamamlandıktan sonra Verifier çalışır; ardından Lead bulgularını `thinking-model-combination` ile sentezleyerek tek bir nihai karar (`40-verdict.md`) ve önceliklendirilmiş eylem planı üretir; plan `Agent/plan.md`'ye, çıkarımlar `Agent/memory.md`'ye işlenir.
   - **Otonom Baş Mimar (Lead Architect Inception):** Sıfır dizinde yeni bir fikir verildiğinde; `sherlock-literature` ile web/literatür/Context7 araştırması yapar, `code.md` ve `Agent/` yapısını kurar, bağımlılıkları yükler ve `scripts/` mimarisini modüler olarak sıfırdan dizayn eder.
   - **Sürekli Geliştirme & Anti-Duplikasyon:** Yeni özellik taleplerinde `Agent/` hafızasını tarar, fonksiyonları doğru modüle ekler; duplikasyon, ölü kod veya hardcoded bypass oluşturmaz.
   - **Sürekli Mimari Gözetim & Aşınma Alarmı (Drift Guardian):** Sistem dosya boyutlarını (>1.400 satır), duplikasyonları ve anayasal kurallardan sapmaları sürekli izler. Yapıdan uzaklaşma başladığında kullanıcıyı anında uyararak refactoring / anayasa onarımı teklif eder.
   - **Evrensel Anka Protokolü (Phoenix Constitution Engine):** Herhangi bir repoda `code.md` eksikse sıfırdan inşa eder (`--bootstrap-constitution`), aşınma varsa orijinal 5 yasaya uygun olarak onarır (`--audit-constitution`).

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
       -> 6_SUBAGENT_SHERLOCK_AUDIT
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
5. **Yasa 5 (Sherlock 6-Ajanlı Çekişmeli Denetim):** Testler gerçek runtime çağrısı yapar (`FAIL-PAPER-TIGER-TEST` kalkanı).
6. **Yasa 6 (Kısmi İyileşmeyi Koruma ve Artımlı İlerleme):** Bir patch genel başarımda net bir iyileşme sağlıyorsa (örn: 3 vaka yerine 6 vaka geçiyorsa), panikle tamamen geri çekilmez (rollback yapılmaz); ilerleme yeni baseline kabul edilip kalan vakalar için hedefli mikro-düzeltme uygulanır.
7. **Yasa 7 (Sıfır Çalışma Alanı Kirliliği - Zero Workspace Pollution):** Proje ana dizininde asla geçici scratch veya analiz dosyası oluşturulmaz; tüm geçici analizler sistem artifact alanında yürütülür ve iş bitiminde derhal imha edilir.
8. **Yasa 8 (Hedefli Ölü Kod Temizliği):** Refactoring sonrası oluşan atıl/ölü kodlar temizlenir; temizlik yetkisi yalnızca aktif iş paketinin hedeflediği `FunctionDef` kapsamı ile sınırlıdır.
9. **Yasa 9 (Atomik Rollback Kapsamı & Toptan Yedek Kısıtı):** Ajanlar tüm repoyu kopyalayan toptan yedek (full zip/recursive backup) alamaz; yalnızca aktif iş paketinde değiştirilen tekil dosyanın anlık atomik yedeği (`.bak`) tutulur ve işlem bitince temizlenir.
10. **Yasa 10 (Otonom Hakem Heyetli Skil Evrimi):** `code.md` veya `memory.md` içerisine eklenen yeni mühendislik yaklaşımları, kullanıcıyı onay sorularıyla yormadan Sherlock'un 6 alt ajanı tarafından literatür/web ve adversary stres testleriyle değerlendirilir; faydası kanıtlanan yaklaşımlar otonom olarak küresel skile işlenir.

