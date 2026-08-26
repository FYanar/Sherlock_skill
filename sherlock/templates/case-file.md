# Dava Dosyası — <dava adı>

> **DONMUŞ BELGE.** Tur 1 başladıktan sonra değiştirilmez. Değişmesi gerekirse dava baştan başlatılır.
> 6 uzman ajan da ilk iş olarak `code.md`, `Agent/memory.md` ve bu dosyayı okur; bulgularını buradaki `C<n>` kimliklerine bağlar.

```yaml
case:          <slug>
date:          <YYYY-MM-DD>        # Literatür penceresi bu tarihten 5 yıl geri hesaplanır
mode:          code | plan | manuscript | pipeline | architecture | mixed
review_policy: standard | deep
depth:         standard | deep
target:        <dosya / klasör / diff yolu veya "sohbette verilen metin">
```

## 1. İncelenen Nedir
<İki-üç cümle. Ne olduğu, ne yapmayı amaçladığı, hangi aşamada olduğu.>

## 2. Neden İnceleniyor
<Kullanıcının asıl endişesi ve hedefleri.>

## 3. Başarı Ölçütü
<Bu iş neyi başarırsa "doğru" sayılır? Ölçülebilir ve test edilebilir yazılır.>

## 4. Dava İddiaları (Claims Matrix)

| # | İddia / Sözleşme |
|:---:|---|
| C1 | |
| C2 | |
| C3 | |
| … | |

## 5. Önerilen Değişiklikler ve Etki Alanı

| # | Değişiklik | Beklenen Sistemik Etki |
|:---:|---|---|
| X1 | | |
| X2 | | |

## 6. Kapsam Dışı (Out-of-Scope)
- <…>

## 7. Bilinen Kısıtlar ve Varsayımlar
- <…>

## 8. Erişilebilir Kaynaklar
- <…>

---

## 🏛️ 6 Uzman Ajan Görev Dağılımı — Tur 1

| Ajan Kimliği | Rol ve Odak Alanı | Çıktı Dosyası |
|:---:|---|---|
| `sherlock-structural` | Kod mimarisi, AST, gereksiz karmaşıklık ve Değişim Etki Matrisi | `10-r1-structural.md` |
| `sherlock-literature` | Güncel standartlar, Context7 dokümantasyonu ve kütüphane sözleşmeleri | `10-r1-literature.md` |
| `sherlock-adversary` | Karşı-avukat, 5-12 somut arıza rotası ve pre-mortem | `10-r1-adversary.md` |
| `sherlock-config` | SSOT bütünlüğü, tolerans çelişkileri ve ölü parametreler (`dead keys`) | `10-r1-config.md` |
| `sherlock-test` | Test süiti AST denetimi, TDD uyumu ve anti-paper-tiger kalkanı | `10-r1-test.md` |
| `sherlock-verifier` | 5 ajanın sunduğu kanıtların ham disk ve Bayesçi doğrulaması | `15-r1-verification.md` |

*Not: Tur 1'de araştırmacılar birbirinin raporunu okumaz; bağımsızlık esastır.*
