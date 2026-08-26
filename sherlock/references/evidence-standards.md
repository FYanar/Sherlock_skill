# Sherlock Kanıt Standartları (Evidence Standards 3.0)

Öncelikli uygulayıcı `sherlock-literature`; `sherlock-verifier` aynı eşikleri denetim ölçütü olarak kullanır. Diğer tüm ajanlar da dış kaynak gösterirken bu kurallara uyar.

**Temel İlke:** Çekilmemiş/doğrulanmamış kaynak, kaynak değildir. Bellekten veya eğitim verisinden ezbere atıf yapmak sistemde kural ihlalidir; her referans doğrulanabilir bir kimlik veya resmî URL taşımalıdır.

---

## 1. Güncellik Penceresi (Currency Window)

`00-case.md` dosyasındaki **`date` alanından geriye doğru 5 yıl**. Ajan bu tarihi dava dosyasından okur.
- **5 yıldan eski kaynaklar:** Yalnızca `[FOUNDATIONAL]` etiketiyle ve neden hâlâ geçerli olduğunun gerekçesiyle sunulabilir.
- **Hızlı değişen alanlar:** ML kütüphaneleri, CLI araçları ve API spesifikasyonlarında son 2-3 yılın güncel belgeleri esastır.

---

## 2. Kabul Edilen Yayın ve Standart Kaynakları

Sherlock şu kaynak hiyerarşisini tanır:

1. **PubMed / PMC / NCBI:** Akademik biyotıp ve yaşam bilimleri makaleleri (PMID veya PMCID ile).
2. **Hakemli Dergi Makaleleri:** Crossref veya yayınevi DOI'si ile doğrulanabilir makaleler (`https://doi.org/...`).
3. **Resmî Kılavuzlar ve Endüstri Standartları:**
   - **Biyomedikal & Sağlık:** FDA, EMA, WHO, ICH yönergeleri.
   - **Mühendislik & Yazılım:** ISO, IEEE, RFC, W3C, PEP standartları ve resmî dil/framework spesifikasyonları.
   - *Kural:* PMID/DOI içermeyen standartlar için **doğrulanabilir resmî doküman URL'si veya standart numarası** (Örn: `ISO/IEC 27001:2022`, `RFC 9110`) zorunludur.
4. **Preprint Yayınlar:** bioRxiv, medRxiv, arXiv (`[PREPRINT]` etiketi ile).
5. **Kütüphane / API / SDK Dokümantasyonu:**
   - **Öncelik:** Context7 MCP (`resolve-library-id` $\to$ `query-docs`).
   - **Yedek (Fallback):** Web araması (`search_web` / `read_url_content`) veya yerel paket dokümantasyonu.

---

## 3. GitHub ve Açık Kaynak Repoları

Bir GitHub reposu çözüm veya kanıt olarak gösterilecekse şu alanlar raporlanır:
`Yıldız Sayısı · Son Commit (pushed_at) · Lisans · Açık Issue Durumu · Arşivli mi?`

| Etiket | Tanım |
|---|---|
| `[STALE]` | 18 aydan uzun süredir commit almamış repo. |
| `[ARCHIVED]` | Sahibi tarafından arşivlenmiş/terk edilmiş repo. |
| `[LOW-ADOPTION]` | <200 yıldız (Eğer alanın açık kanonik referans implementasyonu değilse). |

Lisans kontrolü zorunludur: Proje lisansıyla çatışan (örn. GPL vs ticari/MIT) bir aracı önermek bulgu konusudur.

---

## 4. Halüsinasyon ve Doğrulama Kapısı

- Atıfsız veya kaynaksız sunulan her dış iddia `[UNVERIFIED]` damgası alır ve **şiddeti en fazla `MINOR`** olabilir.
- Kaynak bulunamadıysa bu dürüstçe belirtilmelidir.
- **Kaynağın yokluğu da meşru bir bulgudur:** *"Son 5 yılda bu algoritmanın doğruluğunu kanıtlayan hakemli bir yayın bulunamadı"* tespiti meşrudur; ancak **arama terimleri, sorgulanan veritabanları ve sonuç sayıları** arama kaydı tablosunda kanıtlanmalıdır.

---

## 5. Zorunlu Arama Kaydı Tablosu

Literatür raporunun (`10-r1-literature.md`) *"Arama Kaydı"* bölümü tekrarlanabilir olmalıdır:

| Kaynak / Veritabanı | Arama Terimi / Sorgu | Filtre | Toplam Sonuç | İncelenen Kaynak Sayısı |
|---|---|---|:---:|:---:|
| Context7 | `/rdkit/rdkit "metal coordination charge"` | latest | 5 snippets | 5 |
| PubMed | `("AutoDock Vina") AND ("zinc coordination")` | 2021-2026 | 42 | 10 |
| GitHub | `vina metal docking` | stars>100 | 8 | 8 |
