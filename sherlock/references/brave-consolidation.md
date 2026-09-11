# Cesur Konsolidasyon Protokolü — Detaylı Uygulama Kılavuzu

> **Felsefe:** Korkak AI her duplikasyonu raporlar ama silmez → çöplük büyür. Cesur AI emin olduğu hatayı sormadan düzeltir, testlerle doğrular, bozulursa yedekten geri alır. **Cesur ama aptal değil.**

---

## 1. Ne Zaman Silinir, Ne Zaman Silinmez?

### SİL (Cesur Mod — sormadan)

- `calculateTotal()` ve `computeSum()` → AST gövdesi byte-byte aynı, parametreler aynı, yan etki aynı, Graphify aynı community, poliglot taramada farklı domain tipi yok → **HIGH_CONFIDENCE**
- B'yi çağıran 4 yer bulundu, hepsi A'ya rewire edilebilir, compile + test geçiyor → **SİL B'Yİ, REWIRE ET**

### SİLME (Klasik Mod — raporla, sor)

- `formatDate()` vs `formatDateForDisplay()` → isim benzer ama biri timezone ekliyor, diğeri eklemiyor → semantik ayrışma → **SİLME, bağımsız tut**
- `getUser()` vs `get_user()` → biri `None` döner, diğeri exception fırlatır → sözleşme farklı → **SİLME**
- Graphify `INFERRED` edge ile eşleşenler → **UNVERIFIABLE** → Cesur Mod YASAK
- `Agent/memory.md`'de geçmişte benzer konsolidasyon rollback yemişse → **DİKKAT, aynı hatayı tekrarlama**

---

## 2. Grounding — Projenin Yönünü Anlama (Zorunlu İlk Adım)

Cesur Mod'a girmeden önce şu 3 dosyayı OKUMAK ZORUNDASIN:

1. **`code.md`** — Proje anayasası: mimari prensipler, SSOT, fail-closed sözleşmesi
2. **`Agent/plan.md`** — Aktif plan: proje nereye gidiyor? Hangi modül genişleyecek? Silinecek şey gelecek planla çelişiyor mu?
3. **`Agent/memory.md`** — Geçmiş dersler: daha önce hangi konsolidasyonlar denendi, hangileri rollback yedi, hangi pattern'ler tehlikeli?

**Örnek:** `memory.md`'de "2024-03: `utils/format.py` konsolidasyonu rollback yedi, çünkü `legacy_api` hala onu çağırıyordu" yazıyorsa → aynı pattern'i tekrarlarken ekstra poliglot tarama yap.

Grounding yapmadan Cesur Mod'a girmek **YASAKTIR**.

---

## 3. Semantik Eşdeğerlik Kanıtı — Nasıl Emin Olunur?

Sadece isim benzerliği yetmez. Şu 3 kanıttan **en az 2'si** olmalı:

| Kanıt | Nasıl Toplanır | Eşik |
|---|---|---|
| **AST Eşdeğerliği** | `graphify_adapter.py` veya doğrudan `ast` parse → gövde normalize edilip karşılaştırılır | Byte-byte aynı (whitespace/comment hariç) |
| **Graphify Community** | `graphify-out/graph.json` → A ve B aynı community'de, aynı edge set'i | Aynı community + cohesion >0.5 |
| **Davranışsal Test** | Aynı girdi setiyle A ve B'yi çalıştır, çıktı/yan etki karşılaştır | 10+ girdi, %100 eşleşme |

**Red flag'ler (bunlardan biri varsa SİLME):**
- Parametre tipi farklı (`str` vs `row_like`)
- Dönüş tipi farklı (`None` vs `False`)
- Biri `async`, diğeri sync
- Biri `fix.py` gibi izole ACID motorunda (bağımsız kalmalı)

---

## 4. Rewire Haritası — Çağrı Noktalarını Bulma

B'yi silmeden önce B'yi çağıran **her yeri** bul:

```
1. AST taraması: from X import B, import B, B(
2. Poliglot: .bat, .sh, .ps1, .cmd, Makefile, Dockerfile, .github/workflows
3. Heredoc: <<'PY', python -c "from X import B"
4. Dinamik: getattr, __import__, importlib, globals()[]
5. Re-export: __init__.py, facade, alias (_alias = B)
```

Harita eksikse → Cesur Mod YASAK. Eksik rewire = runtime patlaması.

---

## 5. Atomik İcra ve Doğrulama

```python
# Pseudo
backup_path = create_verified_zip(target_dir)  # Pillar 1
try:
    atomic_rewire(B_callsites -> A)  # tek transaction
    delete(B_definition)
    run("python -m py_compile <changed_files>")  # Pillar 6
    run("pytest tests/test_relevant.py -xvs")  # veya npm/cargo test
    run("python scripts/graphify_adapter.py --ensure")  # graph kopuk mu?
    # HEPSİ GEÇTİ → success
    write_finding("F-C-BRAVE-CONSOLIDATION", CONFIRMED)
    append_memory("BRAVE-CONSOLIDATION: B -> A, <tarih>, <sebep>, <test sonucu>")
except Failure as e:
    rollback(backup_path)  # OTOMATİK, SORMADAN
    write_finding("F-C-BRAVE-ROLLBACK", CONFIRMED)
    append_memory("BRAVE-FAILED: B->A rollback, sebep: <e>, ders: <öğrenilen>")
    # ASLA bozuk halde bırakma
```

**Test stratejisi:**
- Değişen modülün doğrudan testleri
- `graphify path A <dependent>` ile bulunan bağımlı modüllerin testleri
- En az 1 happy-path + 1 edge-case testi

---

## 6. Agent/memory.md Ders Formatı

Her Cesur icra sonrası memory.md'ye şu formatta ders eklenir:

```markdown
### BRAVE-CONSOLIDATION 2026-09-01
- Kaynak: `utils/helpers.py::computeSum` (B) → `core/calc.py::calculateTotal` (A)
- Kanıt: AST identical (SHA: abc123), Graphify community 3, 12 girdi testi %100 eşdeğer
- Rewire: 4 call-site (2× .py, 1× START.bat, 1× tests/test_calc.py)
- Doğrulama: py_compile ✅, pytest 12 passed ✅
- Sonuç: CONFIRMED, yedek: backups/core_pre_brave_20260901_101500.zip

### BRAVE-FAILED 2026-09-01
- Kaynak: `api/format.py::formatDate` → `utils/date.py::formatDateForDisplay`
- Sebep: rollback — semantik ayrışma kaçmış, timezone farkı testte yakalandı
- Ders: Tarih fonksiyonlarında timezone parametresi varsa Cesur Mod'a girme
```

Bir sonraki davada bu dersler okunarak aynı hata tekrarlanmaz.

---

## 7. Research & Verify (F-R) Kontrolü

Research & Verify (`F-R`) her BRAVE bulgusunu şu hiyerarşiye göre damgalar:

- **CONFIRMED:** yedek var + AST identical + test geçti + graph kopuk değil
- **REFUTED:** test/compile patladı ama rollback yapılmamış (bozuk bırakılmış) → BLOCKER
- **UNVERIFIABLE:** INFERRED edge ile silinmiş veya poliglot tarama eksik → derhal rollback öner
