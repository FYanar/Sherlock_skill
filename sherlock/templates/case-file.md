# Dava Dosyası — <dava adı>

> **DONMUŞ BELGE.** Tur 1 başladıktan sonra değiştirilmez.
> **Asimetrik Bağlam Kuralı:** Code Analyst `code.md`, `Agent/memory.md`, bu dosyayı (§9 dahil) ve
> `.sherlock/graphify-context.md` okur. Adversary ve Research & Verify ise yalnızca bu dosyayı (§9 dahil),
> `.sherlock/graphify-context.md` ve görevlerine ait özetleri okur (tam memory/code.md okumaz, token korur).
> Bulgular mutlaka `C<n>` iddialarına bağlanır; Graph okumadan yazılan bulgu geçersizdir.

```yaml
case:          <slug>
date:          <YYYY-MM-DD>
mode:          code | plan | manuscript | pipeline | architecture | mixed
depth:         standard | deep
depth-kaynak:  flag | nl-deep:<eşleşen kelime> | nl-lite | heuristik
target:        <dosya / klasör / diff yolu veya "sohbette verilen metin">
```

> **v5.1 NL Depth Notu:** `depth` Lead tarafından NL çıkarımıyla doldurulur. `deep/derin/literatür/makale/pubmed/doi/standart/güncel/kapsamlı/detaylı/araştır/doğrula` geçiyorsa `deep`, sadece `hızlı/quick/üstünkörü/typo` geçiyorsa Lite adayı. `depth-kaynak` hangi kuralın tetiklendiğini mühürler.

## 1. İncelenen Nedir
<İki-üç cümle.>

## 2. Neden İnceleniyor
<Kullanıcının endişesi ve hedefleri.>

## 3. Başarı Ölçütü
<Ölçülebilir ve test edilebilir.>

## 4. Dava İddiaları (Claims Matrix)

| # | İddia / Sözleşme |
|:---:|---|
| C1 | |
| C2 | |
| C3 | |

## 5. Önerilen Değişiklikler ve Etki Alanı

| # | Değişiklik | Beklenen Sistemik Etki |
|:---:|---|---|
| X1 | | |

## 6. Kapsam Dışı (Out-of-Scope)
- <…>

## 7. Bilinen Kısıtlar ve Varsayımlar
- <…>

## 8. Erişilebilir Kaynaklar
- <…>

---

## 🏛️ 3 Uzman Ajan Görev Dağılımı — Tur 1

| Ajan Kimliği | Rol ve Odak Alanı | Çıktı Dosyası |
|:---:|---|---|
| `code-analyst` | Mimari/AST, SSOT/konfigürasyon, test kalitesi, dead code, duplikasyon | `10-r1-code-analyst.md` |
| `adversary` | Karşı-avukat, arıza rotaları, pre-mortem | `10-r1-adversary.md` |
| `research-verify` | Standartlar, literatür, kanıt doğrulama | `10-r1-research-verify.md` |

*Not: 2+1 bariyerli yürütülür. Code Analyst ve Adversary paralel çalışır; Research & Verify her iki rapor tamamlandıktan sonra devreye girerek bulguları doğrular.*

---

## 9. Graphify SSOT (Otomatik — graphify_adapter.py tarafından doldurulur)

- **graph.json SHA256:** `<sha veya MISSING>`
- **Stats:** `<N nodes, M edges veya MISSING>`
- **God Nodes (top 5):** `<tablo veya yok>`
- **Communities:** `<N adet veya yok>`
- **Durum:** `GRAPHIFY_ACTIVE` | `GRAPHIFY_MISSING_FALLBACK`

```markdown
<!-- graphify-context.md içeriği buraya inject edilir -->
```
