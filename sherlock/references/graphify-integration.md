# Sherlock x Graphify Entegrasyon Protokolü

> **Amaç:** Sherlock'un 3 ajanlı (2+1 bariyerli) adli tıp protokolünde AST/semantik keşfi Graphify'a devretmek, Sherlock'u tüketici ve hakem katmanına odaklamak.
> **Kaynak:** https://github.com/Graphify-Labs/graphify — PyPI `graphifyy` (çift y), CLI `graphify`.

---

## 0. Kurulum — Otomatik ve Manuel (GitHub README'ye göre)

**Gereksinim:** Python 3.10+ ve Claude Code / OpenCode / herhangi bir AI agent host.

**Otomatik (Sherlock yapar):** `scripts/graphify_adapter.py --ensure` çağrıldığında CLI yoksa otomatik kurar:

```python
# Adapter deneme sırası:
uv tool install graphifyy -q          # uv varsa
pipx install graphifyy                # pipx varsa (Windows/macOS externally-managed için önerilen)
pip install graphifyy -q              # standart
pip install graphifyy -q --break-system-packages  # Linux fallback
```

**Manuel (kullanıcı):**
```bash
pip install graphifyy && graphify install          # standart
pipx install graphifyy                              # Windows: PATH sorunu yaşamamak için önerilen
# Windows PATH sorunu: %APPDATA%\Python\Python3xx\Scripts PATH'e eklenmeli (örn Python313)
# macOS externally-managed: pipx install graphifyy
```

**Doğrulama:**
```bash
graphify --help          # CLI var mı?
pip show graphifyy        # PyPI paketi (versiyon 0.9.53+)
python -m graphify --help # fallback
```

**Not:** PyPI adı geçici olarak `graphifyy` (çift y), CLI ve skill komutu `graphify` olarak kalır. `pip show graphify` boş döner — doğrusu `pip show graphifyy`.

---

## 0.1 Graphify Ne Yapar — Yetenek Matrisi

| Dosya Tipi | Uzantı | Çıkarım |
|---|---|---|
| Code | `.py .ts .js .go .rs .java .c .cpp .rb .cs .kt .scala .php` | AST via tree-sitter + call-graph |
| Docs | `.md .txt .rst` | Kavram + ilişki (Claude LLM) |
| Papers | `.pdf` | Citation mining + concept extraction |
| Images | `.png .jpg .webp .gif` | Claude vision (screenshot, diagram, her dil) |

**Çıktılar (`graphify-out/`):**
| Dosya | Açıklama |
|---|---|
| `graph.json` | SSOT — kalıcı graph, haftalar sonra query edilebilir |
| `GRAPH_REPORT.md` | God nodes, surprising connections, suggested questions |
| `graph.html` | İnteraktif viz (click, search, community filter) |
| `CALLFLOW.html` | Mermaid interaktif çağrı akışı, arayüz tabloları ve mimari şema |
| `pipeline_graph.html` | Y-şekilli aşama akışı, hub izolasyonu ve filtreli Vis.js grafiği |
| `cache/` | SHA256 cache — sadece değişen dosyalar re-extract edilir |
| `obsidian/` | `--obsidian` ile Obsidian vault |
| `wiki/` | `--wiki` ile agent-crawlable wiki (index.md + community makaleleri) |

**Komutlar (Sherlock'un kullandıkları vurgulu):**
| Komut | Ne yapar | Sherlock |
|---|---|---|
| `graphify .` / `graphify ./raw` | Klasörü tara, graph üret | **Pre-Flight SSOT** |
| `graphify ./raw --mode deep` | Daha agresif INFERRED edge | Derin mod davalar |
| `graphify ./raw --update` | Sadece değişen dosyaları re-extract | Incremental turlarda |
| `graphify query "soru"` | BFS traversal — soruyu graph'tan cevapla | **F-R, F-C** |
| `graphify path "A" "B"` | İki node arası en kısa yol | **F-A blast radius** |
| `graphify explain "X"` | Node'un komşularıyla açıklaması | **F-R** |
| `graphify affected "X"` | Reverse traversal — X'ten etkilenenler | **F-A regresyon** |
| `graphify god-nodes --top 10` | En bağlı hub'lar | **F-C monolit** |
| `graphify extract <path> --code-only` | Sadece AST, LLM yok (CI headless) | **CI / fallback** |
| `graphify add <url>` | URL fetch et, ./raw'a kaydet, graph update | Opsiyonel |
| `graphify hook install` | post-commit hook (her commit'te rebuild) | Opsiyonel auto-sync |
| `graphify --watch` | Dosya değiştikçe otomatik rebuild | Paralel ajanlarda |
| `graphify export html/svg/graphml` | Export formatları | Raporlama |

**Önemli:** Her edge `EXTRACTED` / `INFERRED` / `AMBIGUOUS` etiketli — ne bulundu vs ne tahmin edildi şeffaf. Code-only corpus'ta LLM gerekmez (0 token).

---

## 1. Mimari Karar

```
ÖNCE:  Sherlock (her ajan kendi AST taramasını yapar)  →  5× tekrar, kör, pahalı
SONRA: Graphify (SSOT: graph.json + GRAPH_REPORT.md)  →  Sherlock (tüketir, doğrular, hüküm verir)
```

- **SSOT:** `graphify-out/graph.json` (SHA256 ile mühürlenir)
- **Türevler:** `GRAPH_REPORT.md` (god nodes, communities, surprising connections), `.graphify_analysis.json`, `.graphify_labels.json`
- **Adapter:** `scripts/graphify_adapter.py` → `.sherlock/graphify-context.md` + `.sherlock/graphify-findings.json`

**Kural:** Graphify yoksa Sherlock fallback modda çalışır (eski AST taraması). Graphify varsa **öncelik graphify'dır**.

---

## 2. Pre-Flight Hook (AŞAMA 0)

`bootstrap_constitution.py` ve `SKILL.md` AŞAMA 0'a eklenen adım:

```python
# Pseudo
from scripts.graphify_adapter import ensure_graphify, build_context_md
status = ensure_graphify(workspace, no_viz=True)
ctx = build_context_md(workspace)
# status ve ctx yolu 00-case.md'ye inject edilir
```

- `graphify` CLI yoksa → **otomatik `pip install graphifyy`** denenir (pipx → pip → --break-system-packages → uv sırası)
- `graph.json` yoksa → `graphify . --no-viz` (LLM gerektirmez, sadece AST, ~5-30sn)
- `graph.json` varsa ve <24h → cache kullan
- `graph.json` >24h veya `--update` flag'i → tazele

---

## 3. Ajan Bazlı Entegrasyon Matrisi

| Ajan (kanonik 3'lü) | Eski Kaynak | Yeni SSOT Kaynağı | Bulgu Dönüşümü | Kanıt Standardı |
|---|---|---|---|---|
| **F-C Code Analyst (Structural+Config+Test birleşik)** | `rg + AST`, `config.yaml`, `tests/` | `graph.json` nodes/edges + `gods` + `communities` + config node'ları + `gods` vs `tests/` coverage | `degree>30` → `F-C-GOD-01 BLOCKER` (monolit); `cohesion<0.3` → modüler ayrışma/SSOT ihlali; isolated node → dead-key adayı; god'a test yoksa `F-C-MISSING-COVERAGE` | `EXTRACTED` edge = CONFIRMED, `INFERRED` = UNVERIFIABLE; `F-C-COHESION-*` |
| **F-R Research & Verify (Literature+Verifier birleşik)** | `search_web + Context7`, ham disk/log | `graphify query` (proje terminolojisi) + sonra `search_web/Context7` (dış standart); `graph.json` SHA256 + `source_location` | Önce iç terminolojiyi graph'tan doğrula, sonra dış kaynakla karşılaştır; her bulgunun `source_location`'ını SHA ile doğrula; `INFERRED` edge'leri REFUTE/UNVERIFIABLE'a düşür | `[CANLI ARAMA KANITI]` + Bayesçi damgalama |
| **F-A Adversary** | Tahmini pre-mortem | `gods` (SPOF) + `surprises` (gizli coupling) + `graphify path A B` | God node = tek hata noktası arıza rotası, surprising edge = sessiz regresyon | Her arıza rotası için `graphify path` çıktısı falsifier |

---

## 4. Kanıt Hiyerarşisi (Evidence Standards Uyumu)

`references/evidence-standards.md`'ye ek:

- **CONFIRMED:** `graph.json` içinde `type: "EXTRACTED"` veya `origin: "AST"` olan edge/node + `source_location` dosya+satır eşleşiyor
- **UNVERIFIABLE:** `type: "INFERRED"` veya `confidence < 0.7` olan edge'ler (LLM semantik çıkarımı)
- **REFUTED:** `graphify query` boş dönerse veya `path` bulunamazsa

Research & Verify bu hiyerarşiyi uygular ve `10-r1-research-verify.md` raporunda her bulguya damga vurur.

---

## 5. Dava Dosyası Entegrasyonu (00-case.md)

`templates/case-file.md`'ye eklenen bölüm:

```markdown
## 9. Graphify SSOT (Otomatik - graphify_adapter.py tarafından doldurulur)
- graph.json SHA: <sha>
- Stats: <N nodes, M edges>
- God Nodes: <tablo>
- Communities: <tablo>
- Kaynak: .sherlock/graphify-context.md
```

Ajanlar `00-case.md`'yi okuduğunda bu bölümü **zorunlu** okur. Yoksa fallback modda çalışır.

---

## 6. Fallback Protokolü

```
if graphify-out/graph.json exists and valid:
    use graphify SSOT (primary)
else:
    log "[GRAPHIFY-MISSING] Fallback to legacy AST scan"
    ajanlar eski yöntemle çalışır (rg, AST)
    bulgulara [NO-GRAPHIFY-FALLBACK] etiketi eklenir
```

Fallback asla hata vermez, sadece uyarı üretir. Sherlock Graphify olmadan da çalışabilir.

---

## 7. Maliyet ve Performans

- **Code-only corpus:** Graphify sadece AST çıkarır → **0 token, 0 API key**, ~5-30sn (Sherlock'un varsayılanı)
- **Docs/papers/images corpus:** Semantik extraction için `GEMINI_API_KEY` varsa Gemini, yoksa host LLM → token maliyeti var ama Sherlock'un 5 ajanının 5× taramasından daha ucuz
- **Cache:** `graphify.cache` sadece değişen dosyaları re-extract eder → ikinci dava %90 daha hızlı
- **71.5x token reduction:** Karpathy repos + papers + images corpus'unda (52 dosya) naive full-read'e göre

---

## 8. Dosya Sözleşmesi

| Dosya | Üreten | Tüketen | Açıklama |
|---|---|---|---|
| `graphify-out/graph.json` | Graphify | Adapter + 3 ajan | SSOT |
| `graphify-out/GRAPH_REPORT.md` | Graphify | Adapter, F-R, F-A | İnsan okunabilir özet |
| `graphify-out/graph.html` | Graphify | Kullanıcı / Geliştirici | Vis.js standart ağ topolojisi |
| `graphify-out/CALLFLOW.html` | Graphify export | Kullanıcı / Mimar | Mermaid çağrı akışları ve arayüz tabloları |
| `graphify-out/pipeline_graph.html` | `pipeline_visualizer.py` | Kullanıcı / Mimar | Y-şekilli aşama akışı ve hub filtreli interaktif viz |
| `.sherlock/graphify-context.md` | `graphify_adapter.py` | `00-case.md` + 3 ajan | Normalize edilmiş SSOT özeti |
| `.sherlock/graphify-findings.json` | `graphify_adapter.py` | F-R, F-A, F-C | Otomatik bulgu önerileri (opsiyonel) |
| `.sherlock/graphify-context.sha256` | Adapter | Verifier | Mühür |

---

## 9. Doğrulama Checklist

- [ ] `pip show graphifyy` → versiyon görünüyor (örn 0.9.53)
- [ ] `graphify --help` → komut listesi geliyor
- [ ] `graphify_adapter.py --workspace . --ensure` sorunsuz çalışıyor
- [ ] `.sherlock/graphify-context.md` oluşuyor ve `00-case.md`'ye inject ediliyor
- [ ] F-C bulguları `source_location: graphify-out/graph.json#node:<id>` içeriyor
- [ ] F-R `INFERRED` edge'leri UNVERIFIABLE'a düşürüyor
- [ ] Graphify yokken fallback uyarısı üretiliyor, dava bloklanmıyor
