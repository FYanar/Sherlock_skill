---
name: sherlock
description: /sherlock çağrısında 3 hafif uzman alt ajanı (Code Analyst, Adversary, Research & Verify) define_subagent ile devreye sokan, aşamalı adli tıp denetimi, NL depth çıkarımı, Baş Mimar ve Evrensel Anka Protokolü 5.1.
---

# Sherlock v5.1 (Lead Architect, 3-Uzman Alt Ajan, Self-Learning & Self-Pruning + NL Depth)

> Revizyon notu (v5.0 Süper Zeki Yükseltme): v4.2 üzerine — skorlu hafıza (`memory_manager.py`), onaylı evrim (`autonomous_evolution.py` v5), otomatik deadcode tarayıcı (`deadcode_scanner.py`), literatür kapısı (`literature_guard.py` Context7+PubMed), akıllı embedded router (max 2-3 skill/dava) ve meta-dava `--self-audit` eklendi. Kanonik ajan sayısı yine 3'tür; 2+1 bariyer + asimetrik bağlam korunur.

Sherlock; üç bağımsız uzman (**Code Analyst**, **Adversary**, **Research & Verify**) ve bir **Lead Architect** ile çalışan, adli tıp denetimine kadar tüm yaşam döngüsünü yöneten otonom mühendislik protokolüdür.

---

## 🚦 Hızlı Triage Kapısı (Sherlock-Lite vs Full Forensic)

Lead Architect her `/sherlock` çağrısında hedefin kapsamını değerlendirir:

| Mod | Kapsam | Yürütme Modeli | Token & Süre |
|---|---|---|:---:|
| **Sherlock-Lite** (`--lite` veya basit iş veya NL-lite) | Tekil fonksiyon/dosya, <50 satır diff, basit hata, NIT/MINOR inceleme | Alt ajan başlatılmaz. Lead Architect taze AST/Graphify önbelleğiyle doğrudan tek geçişli analiz yapar, kısa `40-verdict.md` üretir. | ~2k token, <15 sn |
| **Full Forensic** (Standart / `--deep` veya NL-deep) | Mimari refactoring, çoklu dosya bağımlılığı, anayasal/SSOT riski, SPOF, literatür/standart doğrulama ihtiyacı | 2+1 bariyerli 3 uzman ajan (`define_subagent`), dava dosyası mühürleme ve çoklu hakem sentezi. `depth` NL çıkarımıyla otomatik set edilir (`standard` vs `deep`). | Standart / Derin bütçe |
| **🧹 Deadcode & Duplikasyon** (`--deadcode` veya NL tetikleyici) | Ölü kod + kopya kod süpürme, workspace geneli | **Full Forensic zorunlu + taze Graph + `deadcode_scanner.py` + 3-kanıt korelasyonu. Lite YASAK. Onay kapısı zorunlu: bul → sun → onay → temizle.** | Derin bütçe |

> **NL Tetikleyici → `--deadcode` eşlemesi (en zeki kısım):** Kullanıcı `/sherlock` ile birlikte şu kalıplardan birini söylerse (`deadkod`, `deadcode`, `dead code`, `ölü kod`, `kullanılmayan`, `duplikasyon`, `duplication`, `tekrar eden kod`, `kopya fonksiyon`, `temizlik`, `süpür`, `konsolide et`, `kullanılmayan dosya/fonksiyonları bul`) Lead Architect bunu **otomatik `--deadcode` davası** sayar, kullanıcı `--deadcode` yazmasa bile aşağıdaki 🧹 protokolünü çalıştırır. Asla Lite'a düşürmez.

> **NL Tetikleyici → `depth: deep` eşlemesi (v5.1 NL çıkarımı, flag yazmak yok):** Kullanıcı `--deep` yazmasa bile aşağıdaki kalıplardan BİRİ geçiyorsa Lead Architect `00-case.md` içine `depth: deep` yazar ve R&V canlı aramaya geçer (Context7 + search_web + literature_guard). Kalıplar (TR/EN, küçük harfe çevir, ek/köklere duyarsız bak):
> - `deep`, `derin`, `derinlemesine`, `derinlemesine araştır`, `deep mod`, `deep moda geç`, `deep modda araştır`, `derinde ara`
> - `literatür`, `literatur`, `literatüre aykırı`, `makale`, `pubmed`, `doi`, `pmid`, `hakemli`, `kaynak göster`, `referans`, `kanıtla`, `doğrula`, `verify`
> - `standart`, `standard`, `güncel`, `guncel`, `canonical`, `best practice`, `context7`, `api dok`, `doküman`, `kapsamlı`, `kapsamli`, `detaylı`, `detayli`, `kapsamlı araştır`, `araştır`, `arastir`
> - Örnek: `sherlock şimdi sırada ligand hazırlamayla ilgili tüm fonksiyonları incele. burda sence literatüre aykırı bişey var mı?` → içinde `literatür` geçtiği için **otomatik `depth: deep`**, kullanıcı `--deep` yazmasa bile.
> - Bu eşleşme `--deadcode` ile çakışırsa önce `--deadcode` (o da zaten `depth: deep` açar, Faz D0).

> **NL Tetikleyici → Lite niyeti:** Kullanıcı `hızlı`, `hizli`, `hızlıca`, `quick`, `üstünkörü`, `üstünkörü bak`, `tek bakış`, `göz gezdir`, `typo`, `yazım`, `küçük hata`, `lite` derse ve yukarıdaki deep/deadcode kalıplarından HİÇBİRİ yoksa Lead Architect Lite'a düşebilir. Deep kalıbı varsa Deep kazanır (Lite YASAK).
>
> **Öncelik sırası (deterministik):** `açık flag (--lite/--deep/--deadcode)` > `NL-deadcode` > `NL-deep` > `NL-lite` > `otomatik heuristik (<50 satır, typo)`. Çakışmada üstteki kazanır ve karar `00-case.md §0` içine `depth-kaynak: flag | nl-deep:<eşleşen kelime> | nl-lite | heuristik` olarak mühürlenir.

---

## 🏛️ 3 Uzman Alt Ajan (Full Forensic Modunda)

| Simge | Ajan | Rol Dosyası | Odak | Önek | Araç İzni |
|:---:|---|---|---|:---:|:---:|
| 🏗️ | **Code Analyst** | `roles/sherlock-code-analyst.toml` | Mimari/AST, SSOT/config, test kalitesi, dead code, duplikasyon, Cesur Konsolidasyon | `F-C` | `write: true` |
| ⚡ | **Adversary** | `roles/sherlock-adversary.toml` | "Nasıl çöker?", arıza rotaları, pre-mortem, regresyon tuzakları | `F-A` | `write: false` |
| 📚 | **Research & Verify** | `roles/sherlock-research-verify.toml` | Standartlar, literatür, kanıt doğrulama, Bayesçi damgalama | `F-R` | `write: false` |

---

## 🛑 Deterministik Yürütme Akışı

```
[/sherlock Çağrısı]
       │
       ▼
 [Triage Kapısı: Kapsam Basit mi?] ──► EVET ──► [Sherlock-Lite: Tek Geçişli Verdict]
       │ HAYIR
       ▼
 AŞAMA 0: Ön-Uçuş (code.md + Agent/ kontrol, Graphify SSOT --ensure)
       │
       ▼
 AŞAMA 1: Dava Dosyası (.sherlock/<YYYYMMDD-slug>/00-case.md)
       │
       ▼
 AŞAMA 2a: Tur 1A Paralel (Code Analyst + Adversary)
       │
      [BARRIER: Raporların diske yazılması beklenir]
       │
 AŞAMA 2b: Tur 1B Doğrulama (Research & Verify)
       │
       ▼
 AŞAMA 3: Lead Merge + Verdict + Hafıza Senkronizasyonu
```

### 🚦 Triage Kapısı (Sherlock-Lite vs Full 3-Ajan Kararı + NL Depth Çıkarımı)

Lead Architect her davanın başında kapsamı + derinliği birlikte değerlendirir (kullanıcıdan flag beklemez, NL çıkarımı yapar):
- **Otomatik Sherlock-Lite Koşulları (TÜMÜ sağlanmalı, deep yoksa):**
  - Kullanıcı açıkça `--lite` verdiyse VEYA NL-lite niyeti varsa (`hızlı/hizli/quick/üstünkörü/tek bakış/göz gezdir/typo/lite`), VE
  - NL-deep kalıplarından HİÇBİRİ yoksa, VE
  - Hedef tek dosya + `<50 satır diff` (`git diff --stat`) VEYA sadece dokümantasyon/typo/NIT ise.
  - NL-deep varsa Lite'a düşmek YASAKTIR (Deep kazanır).
- **Otomatik `depth: deep` Koşulları (BİRİ yeterse):**
  - Kullanıcı açıkça `--deep` verdiyse, VEYA
  - Üstteki NL-deep listesinden biri geçiyorsa (`deep/derin/literatür/makale/pubmed/doi/standart/güncel/context7/kapsamlı/detaylı/araştır/doğrula` vb.), VEYA
  - `--deadcode` davasıysa (zaten deep).
  - Eşleşen kelime `00-case.md §0` içine `depth-kaynak: nl-deep:<kelime>` olarak yazılır.
- **Varsayılan:** Hiçbir tetikleyici yoksa `depth: standard` + kapsam heuristiğine göre Lite/Full kararı.
- **Lite Yürütme Modu:** Alt ajan (`define_subagent`) çağrılmaz. Lead Architect tek geçişte doğrudan analiz yapar, `.sherlock/<case_id>/40-verdict.md` dosyasını özet formatta oluşturur (0 alt ajan maliyeti, minimum kota).
- **Yükseltme Kuralı (Escalate to Full / to Deep):** Lite/standard analiz sırasında gizli SPOF, çoklu modül bağımlılığı, BLOCKER veya literatür şüphesi (`literatüre aykırı olabilir` hissi) çıkarsa derhal Full 3-Ajan + `depth: deep` moduna geçilir, `00-case.md §0` güncellenir (mühür bozulmadan ek not).

---

### 📍 AŞAMA 0: Ön-Uçuş

1. `code.md` ve `Agent/` mevcut mu? Eksikse (Anka inşası):
   ```pwsh
   python {SKILL_DIR}/scripts/bootstrap_constitution.py <workspace>
   ```
   `{SKILL_DIR}` = bu SKILL.md'nin dizini. Audit için:
   ```pwsh
   python {SKILL_DIR}/scripts/bootstrap_constitution.py <workspace> --audit-constitution [--repair]
   ```
2. **Graphify SSOT (Akıllı Önbellek — Token ve Zaman Tasarrufu):**
   ```pwsh
   python {SKILL_DIR}/scripts/graphify_adapter.py --workspace <workspace> --ensure --export-findings
   ```
   - **Varsayılan:** `--ensure` akıllı önbellek kullanır (`graph.json` mevcut ve <24h ise saniyeler içinde 0 tokenle döner).
   - **Koşullu Güncelleme:** Yalnızca `--deep` davalarda, `--force-graph` istendiğinde veya graph >24 saat eskiyse `--auto-update` çalıştırılır.
   - **Tri-Report Görselleştirme Paketi (Otomatik Üretim):** `--ensure`, `--auto-update` veya `--export-reports` çalıştırıldığında `Agent/graphify-out/` (veya `graphify-out/`) altına 3 görsel rapor otomatik senkronize edilir:
     1. `graph.html`: Vis.js standart kuvvet-tabanlı interaktif ağ grafiği (`graphify export html`).
     2. `CALLFLOW.html`: Mermaid tabanlı interaktif çağrı akışı, modüler diyagramlar ve arayüz tabloları (`graphify export callflow-html`).
     3. `pipeline_graph.html`: `pipeline_visualizer.py` tarafından üretilen, gerçek Y-şekilli aşama akışını (Protein Prep + Ligand Prep -> Docking -> Analysis/Benchmark) gösteren, hub filtreli ve arama/denetim panelli Vis.js grafiği.
   - **🧹 `--deadcode` istisnası (en doğru sonuç için):** Deadcode/duplikasyon davasında önbellek GÜVENİLMEZ olabilir (ölü dediğin şey dün silinmiş olabilir). Bu yüzden `--ensure` YERİNE her zaman taze graph zorunludur:
   ```pwsh
   python {SKILL_DIR}/scripts/graphify_adapter.py --workspace <workspace> --auto-update --export-findings
   ```
   `--auto-update` = yaş kontrolsüz koşulsuz `graphify update` (kapsam `.graphify_root`'tan alınır, full-projeye sessiz genişlemez). Graph SHA'sı `00-case.md` §9'a mühürlenir; temizlik sonrası tekrar `--auto-update` çalıştırılıp graph kopukluğu doğrulanır.
   - Kurulum başarısızsa `[GRAPHIFY_MISSING_FALLBACK]` ile devam — dava bloklanmaz (ancak HIGH güven MEDIUM'a düşer, otomatik silme kapanır).

---

### 📍 AŞAMA 1: Dava Dosyası + Depth Mühürleme (NL çıkarımı burada kesinleşir)

`.sherlock/<YYYYMMDD-case-slug>/00-case.md` oluşturulur (`{SKILL_DIR}/templates/case-file.md` şablonundan kopyalanır). Hedef, iddialar matrisi (C1..Cn) yazılır ve mühürlenir.
1. Kullanıcı cümlesini küçük harfe çevir, NL-deep / NL-lite / NL-deadcode listeleriyle tara.
2. `depth:` alanını şuna göre doldur: `nl-deadcode veya nl-deep veya --deep` → `deep`, yoksa `standard`. `depth-kaynak:` satırına hangi kelimenin tetiklediğini yaz (örn. `nl-deep:literatüre aykırı`). Bu satır Tur 1 sonrası değiştirilmez (yükseltme hariç).
3. R&V bu alana bakarak canlı aramaya karar verir; Lead ayrıca R&V promptuna `depth` değerini aynen geçirir.
Ardından §9 Graphify SSOT deterministik doldurulur:
```pwsh
python {SKILL_DIR}/scripts/graphify_adapter.py --workspace <workspace> --inject-case <YYYYMMDD-case-slug>
```

---

### 📍 AŞAMA 2: 3 Uzman Ajan — 2+1 Bariyerli & Asimetrik Bağlam

> [!IMPORTANT]
> - `self` yerine `define_subagent` ile hafif ajan tanımla.
> - **Asimetrik Bağlam Kuralı:** 3 ajana da tüm dosyaları okutma! Yalnızca uzmanlık alanlarına gereken dosyaları sağla (`Code Analyst`: tam anayasa/hafıza; `Adversary` & `R&V`: dava + graphify + özet bağlam).
> - **Bütçe Kuralı:** Her ajan en fazla 5-8 odaklı bulgu raporlar. Kelime tavanları: `Code Analyst` max 800 kelime (3 lens birleşimi), `Adversary` max 600 kelime, `Research & Verify` max 600 kelime.

**Adım 2a — Ajan Tiplerini Tanımla** (ilk çağrıda bir kez):
- `sherlock-code-analyst`: `roles/sherlock-code-analyst.toml` (`enable_write_tools: true`)
- `sherlock-adversary`: `roles/sherlock-adversary.toml` (`enable_write_tools: false`)
- `sherlock-research-verify`: `roles/sherlock-research-verify.toml` (`enable_write_tools: false`)

**Adım 2b-1 — Bariyer Öncesi (C + A Paralel Başlat):**
```json
{
  "Subagents": [
    {
      "TypeName": "sherlock-code-analyst",
      "Role": "Sherlock Code Analyst",
      "Prompt": "code.md, Agent/memory.md, .sherlock/<case_id>/00-case.md ve .sherlock/graphify-context.md oku. God Nodes (degree>30) ve cohesion<0.3 community sınırlarını incele. Max 8 odaklı bulguyla sınırla. Raporunu .sherlock/<case_id>/10-r1-code-analyst.md dosyasına F-C önekiyle yaz; source_location ekle."
    },
    {
      "TypeName": "sherlock-adversary",
      "Role": "Sherlock Adversary",
      "Prompt": ".sherlock/<case_id>/00-case.md iddialarını ve .sherlock/graphify-context.md içindeki God Nodes/Surprising bağlantılarını oku (tam memory/code.md okuma, token koru). En güçlü 5-8 arıza rotasını haritalandır. Raporunu .sherlock/<case_id>/10-r1-adversary.md dosyasına F-A önekiyle yaz."
    }
  ]
}
```

**[BARRIER]:** `sherlock-code-analyst` ve `sherlock-adversary` tamamlanana kadar BEKLE. İki rapor diske mühürlenmeden R&V başlatılamaz!

**Adım 2b-2 — Bariyer Sonrası (Research & Verify Başlat):**
```json
{
  "Subagents": [
    {
      "TypeName": "sherlock-research-verify",
      "Role": "Sherlock Research & Verify",
      "Prompt": ".sherlock/<case_id>/00-case.md (§0 depth + depth-kaynak ve §9 SHA dahil) oku. depth: deep ise (flag veya nl-deep ile set edilmiş olabilir) Context7/search_web canlı araması YAPMAK ZORUNDASIN; depth: standard ise yalnızca yerel/Graphify SSOT terminolojisini kullan (canlı web araması yapma). Şüphede §0 depth-kaynak satırına bak: nl-deep yazıyorsa deep gibi davran. Tamamlanmış .sherlock/<case_id>/10-r1-code-analyst.md ve 10-r1-adversary.md raporlarını oku; her bulgunun source_location ve kanıtını graph.json SHA ve disk düzeyinde sına. Raporunu .sherlock/<case_id>/10-r1-research-verify.md dosyasına F-R önekiyle yaz."
    }
  ]
}
```

**[SUBAGENT_MISSING_FALLBACK]:** Ortamda `define_subagent`/`invoke_subagent` yoksa aynı 3 prompt sıralı çalıştırılır (Code Analyst → Adversary → Research & Verify) ve `[SEQUENTIAL_FALLBACK]` yazılır.

---

### 📍 AŞAMA 3: Lead Merge & Verdict

3 rapor tamamlandıktan sonra Lead Architect:
1. Önce `{SKILL_DIR}/references/merge-rules.md` + `finding-schema.md` + `evidence-standards.md` uygular → deduplikasyon, corroboration escalation (`F-C`, `F-A`, `F-R`).
2. **Graph mühür doğrulaması:** `Agent/graphify-out/graph.json` SHA'sını `00-case.md` §9 ile karşılaştır. Uyuşmazsa `STALE GRAPH` damgala.
3. **Eylem Planı Tasarımı (`20-plan.md` — Koşullu JIT Çözüm Motoru + Akıllı Router):**
   - **Teşhis Disiplini:** Ajanlar hata ararken (Aşama 2) `brainstorming` ve `find-skills` çağıramaz (delilden kopmayı ve token şişmesini önlemek için yasaktır).
   - **Akıllı Embedded Router (v5.0):** Dava tipine göre dava başına max 2-3 embedded skill seçilir, hepsi yüklenmez:
     - God Node / monolit → `thinking-systems + code-simplification`
     - Çöküş / regresyon → `thinking-pre-mortem + thinking-inversion + debugging-and-error-recovery`
     - Standart / doğruluk şüphesi → `source-driven-development + thinking-bayesian`
     - Plan / spec eksikliği → `spec-driven-development + planning-and-task-breakdown`
     - Test zayıflığı → `test-driven-development + goal-verifier`
     - Karar ağacı: `references/embedded_skills/using-agent-skills.md`
   - **Tedavi & Çözüm Üretimi (Aşama 3):**
     - *Basit Düzeltmeler (MINOR/NIT/İzole Fix):* Doğrudan minimal deterministik `fix` yazılır (0 ekstra token).
     - *Karmaşık BLOCKER veya Mimari MAJOR Durumunda:*
       - **`brainstorming` Koşulu:** Eğer çözüm birden fazla mimari trade-off barındırıyorsa (örn. god node parçalama, asenkron vs senkron mimari, katman ayrımı), Lead Architect 2-3 alternatif çözüm rotasını ve trade-off'larını `20-plan.md` içinde açıkça kıyaslar.
       - **`find-skills` Koşulu:** Eğer onarım projenin mevcut AST sınırlarını aşan özel bir domain/araç yetkinliği gerektiriyorsa (örn. veri dönüşümü, ileri güvenlik sertifikasyonu, UI bileşen inşası, performans optimizasyonu), Lead Architect `find-skills` ile ilgili yeteneği tespit eder ve oluşturduğu iş paketine (Work Package) yürütücü uzman beceri olarak atar.
4. `findings.md`, `20-plan.md` üretir ve `{SKILL_DIR}/templates/verdict.md` şablonunu `.sherlock/<case_id>/40-verdict.md` olarak render eder.
5. `Agent/memory.md` ve `Agent/run_state.md` günceller — memory'ye skor etiketi eklenir (`<!-- score:Lxxx uses:N fails:M status:ACTIVE -->`), 1000 satır aşımında `scripts/memory_manager.py --prune` çalıştırılır.
6. Kullanıcıya karar özeti sunar: `GO`, `GO-WITH-CONDITIONS`, `NO-GO` veya `INSUFFICIENT-EVIDENCE`.

**Yükseltme:** Açık BLOCKER / çözülememiş çelişki varsa → Tur 2 (odaklı çapraz sorgu).

---

## 🚀 1. Sıfırdan Proje İnşası

Boş klasörde kullanıcı fikir söylediğinde Lead Architect:
1. **Brainstorming** (`brainstorming` skill): Hedefleri, kısıtları ve başarı ölçütlerini netleştir. 3-5 yaklaşım üret, trade-off'ları karşılaştır, yön seç. Belirsiz fikirle doğrudan implemente etmeye başlama.
2. Derin araştırma (search_web + Context7 + `find-skills` ile projeye özel skill keşfi)
3. `{SKILL_DIR}/scripts/bootstrap_constitution.py <workspace>` → code.md + Agent/ (Anka inşası)
4. Modüler dizin mimarisi tasarımı
5. TDD test süiti ve eylem planı

---

## 🧹 2. Deadcode & Duplikasyon Davası (Graphify + Scanner + 3-Ajan — Onay Kapılı)

> Bu bölüm `--deadcode` davasının kanonik protokolüdür. Tetiklenince AŞAMA 0-3'ün yerine geçmez, **onları bu sırayla özelleştirir:** taze graph → 3-kanıt tarama → 3-ajan forensic → onay raporu → onaylı temizlik.

### Faz D0 — Taze Zemin (Lead Architect, agentsiz)
1. `bootstrap_constitution.py` kontrolü (AŞAMA 0 Adım 1).
2. Taze graph: `graphify_adapter.py --workspace <workspace> --auto-update --export-findings` (önbellek YOK).
3. Dava dosyası aç: `.sherlock/<YYYYMMDD-deadcode>/00-case.md`, `depth: deep`, hedef: `deadcode+duplication sweep`.
4. `--inject-case` ile §9'u mühürle (SHA + stats + god top5).

### Faz D1 — Üçlü Kanıt Tarama (paralel, deterministik — en kapsamlı buluş burada)
Aynı workspace'e 3 bağımsız sinyal aynı anda koşar, hiçbiri tek başına hüküm vermez:
1. **S1 — `deadcode_scanner.py`:** `python {SKILL_DIR}/scripts/deadcode_scanner.py <workspace> --min-lines 3` → `.sherlock/deadcode/<stamp>-report.{json,md}` (HIGH/MEDIUM/LOW + norm_sha duplikasyon grupları + ölü adayları).
2. **S2 — Graphify SSOT:** `.sherlock/graphify-context.md` + `graphify-findings.json` içinden: `isolated node (degree 0)` → ölü adayı; `aynı community + benzer isim + cohesion>0.5` → duplikasyon adayı; `god node` → parçalama adayı (silme adayı DEĞİL).
3. **S3 — Referans doğrulama:** S1+S2'nin her adayı için tam rewire haritası (import + çağrı + poliglot `.bat/.sh/.ps1/.cmd/Makefile/Dockerfile/.github/workflows` + dinamik `getattr/__import__/importlib/globals()` + re-export `__init__.py/__all__/alias`). Bir çağrı noktası bile eksikse aday LOW'a düşer.
**Korelasyon kuralı:** S1(HIGH) + S2(aynı community) + S3(tam harita, sıfır dış çağrı) = `HIGH`; biri eksikse `MEDIUM`; ikisi eksikse `LOW`. Graphify yoksa HIGH verilemez → en fazla MEDIUM.

### Faz D2 — 3-Ajan Forensic (2+1 bariyer, BÜTÇE deadcode'a kilitli)
- **Code Analyst:** S1+S2+S3'ü okur, `brave-consolidation.md` §3'e göre semantik eşdeğerlik kanıtı arar (AST identical + davranışsal test). Max 8 bulgu, her bulguda `source_location + norm_sha + graph community + rewire listesi`. Bu davada rolü **bulmak**, düzeltmek DEĞİL.
- **Adversary:** Her silme/rewire önerisini "nasıl çöker?" diye yıkmaya çalışır: kaçan çağrı noktası, runtime dinamik import, test coverage boşluğu → en güçlü 5-8 arıza rotası.
- **Research & Verify:** Her adayı disk + SHA düzeyinde doğrular, `INFERRED` edge'e dayananı `UNVERIFIABLE`'a düşürür, poliglot taraması eksik olanı reddeder.
**⛔ Bu davada Cesur Mod YASAK:** `brave-consolidation.md`'deki "HIGH ise sormadan sil" kuralı `--deadcode` davasında geçersizdir. HIGH bile olsa AŞAMA 3'e kadar hiçbir dosya değiştirilemez.

### Faz D3 — Onay Raporu (DUR, SUN, BEKLE)
Lead Architect `findings.md` + `40-verdict.md`'yi şu formatta kullanıcıya sunar ve **açık onay bekler** — onay gelmeden Faz D4'e geçmek YASAKTIR:
```markdown
## 🧹 Deadcode & Duplikasyon — Onay Bekliyor (.sherlock/<case_id>/)
- Graph SHA: `<sha>` | Scanner: `<stamp>-report.md` | Sinyal: S1+S2+S3 korelasyonlu
### HIGH (onaylarsan silinir/rewire edilir, yedekli)
- [ ] H1 `path::func` → `path::func` (norm_sha:xxx, community:N, call-sites:M) — kanıt: ...
### MEDIUM (onaylarsan WP'ye girer)
- [ ] M1 ...
### LOW (sadece bilgi, dokunma)
- [ ] L1 ...
Onay formatı: `onaylıyorum: H1,H3,M2` veya `hepsini onayla` veya `vazgeç`
```
Kullanıcı satır satır seçer. `hepsini onayla` bile LOW'ları kapsamaz (LOW asla silinmez).

### Faz D4 — Onaylı Temizlik (sadece onaylanan ID'ler)
1. `create_verified_zip` ile tam yedek (Pillar 1).
2. Sırayla her onaylı ID: `BACKUP → REWIRE → DELETE → VERIFY` (`py_compile` + ilgili testler + `graphify_adapter.py --auto-update` ile graph kopukluk kontrolü).
3. Başarısızlıkta **otomatik rollback**, `BRAVE-FAILED` dersi `Agent/memory.md`'ye yazılır; bozuk halde bırakmak BLOCKER'dır.
4. Başarıda `Agent/memory.md`'ye `BRAVE-CONSOLIDATION` dersi + verdict `GO` güncellemesi.
5. Son taze graph SHA'sı ile `00-case.md` §9 karşılaştırılır, `STALE GRAPH` kalmadığı mühürlenir.

## 🔄 2b. Sürekli Geliştirme & Dead Code Kalkanı

Yeni özellik eklerken:
1. Önce `Agent/structure.md` ve `Agent/memory.md` tara.
2. Benzer fonksiyon varsa yeniden yazma; mevcut olanı genişlet (`graphify query "bu işi yapan var mı?"` ile sor).
3. 7 Aşamalı Dead Code Tasfiye + Cesur Konsolidasyon (detay: `references/brave-consolidation.md`). Normal feature davalarında Cesur Mod geçerlidir; `--deadcode` davasında Faz D3 onay kapısı geçerlidir.

---

## ♦ Anka Protokolü (Phoenix Constitution Engine)

Anka ayrı bir ajan değildir; anayasa motorunun adıdır:
- İnşa: `python {SKILL_DIR}/scripts/bootstrap_constitution.py <workspace>` — `code.md` + `Agent/` yoksa sıfırdan kurar.
- Denetim/onarım: `python {SKILL_DIR}/scripts/bootstrap_constitution.py <workspace> --audit-constitution [--repair]` — 10 evrensel yasaya göre aşınmayı denetler, `--repair` ile eksik yasayı yamalar.
- Hafıza budama: `python {SKILL_DIR}/scripts/bootstrap_constitution.py <workspace> --prune-memory [--memory-budget 1000]` — skorlu FIFO + arşiv.
- Evrim (onaylı): `python {SKILL_DIR}/scripts/autonomous_evolution.py <workspace>` — aday üretir (`.sherlock/evolution/<tarih>-candidates.md`); uygulama: `--apply-approved <E001>` (yedekli, LOCAL_ONLY reddedilir).
- Deadcode: `python {SKILL_DIR}/scripts/deadcode_scanner.py <workspace>` — HIGH/MEDIUM/LOW rapor (`.sherlock/deadcode/`).
- Literatür kapısı: `python {SKILL_DIR}/scripts/literature_guard.py --init-log <workspace>` + `--doi/--pmid/--github/--context7` doğrulama.

---

## 📁 3. Çalışma Alanı Yapısı

### Dava Dosyaları: `.sherlock/<YYYYMMDD-slug>/`
- `00-case.md` — Dava tanımı ve iddialar
- `10-r1-code-analyst.md` — Code Analyst raporu (F-C)
- `10-r1-adversary.md` — Adversary raporu (F-A)
- `10-r1-research-verify.md` — Research & Verify raporu (F-R)
- `findings.md` — Birleştirilmiş bulgular
- `20-plan.md` — Çözüm iş paketleri
- `40-verdict.md` — Nihai karar

### Proje Hafızası: `Agent/`
- `plan.md` — Aktif iş paketleri
- `run_state.md` — Anlık durum
- `memory.md` — Öğrenim beyni (≤1.000 satır, skorlu FIFO via `memory_manager.py`; arşiv `Agent/memory_archive/`)
- `structure.md` & `structure_inventory.md` — Modül envanteri

### Otomatik Raporlar: `.sherlock/`
- `evolution/<tarih>-candidates.md` — Onay bekleyen evrim adayları
- `deadcode/<tarih>-report.md/.json` — HIGH/MEDIUM/LOW temizlik raporu
- `literature/<tarih>-search-log.md` — Tam arama kaydı (R&V özeti buradan)
- `self-audit/<tarih>/` — Meta-dava (SKILL kendi kendini denetler)

---

## 🚀 4. Komutlar

- `/sherlock <hedef>` → Standart 3-Ajanlı (2+1 bariyerli) Denetim. NL çıkarımı aktif: cümlede `deep/derin/literatür/makale/pubmed/standart/güncel/kapsamlı/detaylı/araştır/doğrula` geçiyorsa otomatik `depth: deep`; `hızlı/quick/üstünkörü/typo` geçiyorsa ve deep yoksa Lite adayı.
- `/sherlock --lite <hedef>` → Tek Geçişli Hızlı Denetim (alt ajan yok, anında verdict). NL-deep varsa Lite engellenir.
- `/sherlock deep modda araştır <hedef>` / `/sherlock derinlemesine <hedef>` / `/sherlock literatüre aykırı mı <hedef>` → flag'siz ama otomatik `depth: deep` (NL-deep). `--deep` yazmana gerek yok.
- `/sherlock --deadcode [workspace]` → 🧹 Deadcode & Duplikasyon davası (Faz D0-D4, taze graph + scanner + 3-kanıt + onay kapısı; Lite YASAK, onaysız silme YASAK). NL karşılıkları: `sherlock deadkodları bul`, `ölü kodları temizle`, `duplikasyonları bul`, `kullanılmayanları süpür` — hepsi bu moda girer.
- `/sherlock --deadcode --apply-approved H1,M2 [workspace]` → Faz D4: sadece onaylanan ID'leri temizler (yedekli + verify + rollback).
- `/sherlock --init-project "<fikir>"` → Sıfırdan Proje İnşası (§1)
- `/sherlock --self-audit` → Meta-dava: 3 ajan SKILL/role/template'i denetler (`.sherlock/self-audit/<tarih>/`)
- Anayasa inşası (Anka): `python {SKILL_DIR}/scripts/bootstrap_constitution.py <workspace>` — `/sherlock --bootstrap-constitution` yazımı bu komutun takma adıdır, ayrı bir flag değildir.
- Mimari aşınma denetimi (Anka audit): `python {SKILL_DIR}/scripts/bootstrap_constitution.py <workspace> --audit-constitution [--repair]`
- Hafıza budama: `python {SKILL_DIR}/scripts/bootstrap_constitution.py <workspace> --prune-memory`
- Onaylı skill evrimi: `python {SKILL_DIR}/scripts/autonomous_evolution.py <workspace>` (aday üretir) + `--apply-approved <E001>` (onaylıyı uygular) — `/sherlock --evolve` tarama adımının takma adıdır.
- Rol kurulumu (Codex): `pwsh {SKILL_DIR}/scripts/install-roles.ps1` — `roles/*.toml` → `~/.codex/agents/sherlock-*.toml` (flat layout, SHA-256 doğrulamalı, ACID rollback'li).

---

## 📚 5. Referanslar

- `references/finding-schema.md` — Bulgu formatı ve önek tablosu
- `references/merge-rules.md` — Deterministik birleştirme kuralları
- `references/evidence-standards.md` — Kanıt standartları (v5.0 guard'lı)
- `references/brave-consolidation.md` — Cesur Konsolidasyon Protokolü
- `references/graphify-integration.md` — Graphify SSOT entegrasyonu
- `references/embedded_skills/using-agent-skills.md` — Akıllı router karar ağacı (dava başına max 2-3 skill)
- `scripts/memory_manager.py` — Skorlu hafıza + FIFO enforcement
- `scripts/deadcode_scanner.py` — AST + poliglot + graphify güven raporu
- `scripts/literature_guard.py` — Context7 + PubMed/DOI/GitHub kapısı
- `templates/self-audit.md` — Meta-dava şablonu

---

> [!CAUTION]
> **HİJYEN:** Hiçbir ajan proje kök dizinine `scratch_*`, `temp_*`, `dump_*` dosya yazamaz. Geçici dosyalar `<appDataDir>/brain/<conversation-id>/scratch/` altına yazılır ve iş bitiminde silinir.
