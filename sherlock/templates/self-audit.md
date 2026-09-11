# Sherlock Meta-Dava (Self-Audit) — <tarih>

> **Amaç:** Sherlock'un kendini ayıklaması. 3 ajan SKILL/role/template'i denetler.
> Çıktı: `.sherlock/self-audit/<YYYYMMDD>/` altında bu dosya + `findings.md` + `40-verdict.md`.

```yaml
audit:         <YYYYMMDD>
skill_dir:     <SKILL_DIR>
skill_version: v5.0
mode:          self-audit
```

## 1. Kapsam
- `SKILL.md` sürüm/komut tutarlılığı (v5.0, --self-audit, --prune-memory, --apply-approved var mı?)
- `roles/*.toml` talimat çakışması (6-ajan kalıntısı, şema ihlali)
- `references/*.md` öksüz link (olmayan dosyaya referans)
- `scripts/*.py` çalışabilirlik (`--help` patlıyor mu?)
- `templates/*.tpl` placeholder bütünlüğü

## 2. Ajan Görev Dağılımı

| Ajan | Odak | Çıktı |
|:---:|---|---|
| `code-analyst` | Rol çakışması, şema ihlali, 6-ajan kalıntısı | `10-r1-code-analyst.md` |
| `adversary` | Sequential fallback bağımsızlık kaybı, Lite bypass SPOF, otomatik silme riski | `10-r1-adversary.md` |
| `research-verify` | Evidence-standards ihlali, öksüz link, doğrulanmamış iddia | `10-r1-research-verify.md` |

*2+1 bariyerli yürütülür (C+A paralel → barrier → R&V).*

## 3. Bulgular (F-B önekli patron bulguları dahil)

| # | Bulgu | Şiddet | Doğrulama | Eylem |
|:---:|---|:---:|:---:|---|
| | | | | |

## 4. Karar

**<GO | GO-WITH-CONDITIONS | NO-GO>** — <gerekçe>

## 5. Onay Bekleyen Fix'ler

| # | Dosya | Yama | Risk |
|:---:|---|---|---|
| | | | |

> Otomatik yazma yok. Fix'ler insan onayıyla uygulanır, yedek alınır.
