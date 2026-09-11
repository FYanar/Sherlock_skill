# Hakem Heyeti Kararı (Verdict) — <dava adı>

```yaml
case:          <slug>
date:          <YYYY-MM-DD>
depth:         standard | deep
rounds:        <tur sayısı (1-3)>
verdict:       GO | GO-WITH-CONDITIONS | NO-GO | INSUFFICIENT-EVIDENCE
```

## 1. Nihai Karar ve Gerekçe

**<VERDICT_STAMP>** — <Tek paragraf adli tıp gerekçesi.>

## 2. Koşullar Listesi

*(Yalnızca `GO-WITH-CONDITIONS` için)*

| # | Koşul İfadesi | İlgili Bulgu(lar) | Doğrulama Kriteri |
|:---:|---|---|---|
| K-1 | | F-C1, F-R2 | |

## 3. Öncelikli Eylem Planı

| Sıra | Bulgu | Ajan | Şiddet | Doğrulama | Eylem | Bağımlılık |
|:---:|:---:|:---:|:---:|:---:|---|:---:|
| 1 | F-C1 | Code Analyst | BLOCKER | CONFIRMED | | — |
| 2 | F-A2 | Adversary | MAJOR | CONFIRMED | | 1 |

## 4. Çelişki Defteri Çözüm Durumu

| # | Çelişki | Savunan | Karşı Çıkan | Durum | Kanıt |
|:---:|---|:---:|:---:|:---:|---|

## 5. Reddedilen Bulgular

| Bulgu | İddia | Karşı Kanıt |
|:---:|---|---|

## 6. İzleme Listesi (Watchlist)

| Bulgu | İddia | İzleme Nedeni |
|:---:|---|---|

## 7. Neyi İncelemedik — ZORUNLU

- **Kapsam Dışı:** <…>
- **Erişilemeyen Kaynaklar:** <…>
- **UNVERIFIABLE:**

| Bulgu | Neden Sınanamadı | Sınanması İçin Ne Gerekir |
|:---:|---|---|

## 8. İnceleme İstatistikleri

| Metrik | Tur 1 | Tur 2 | Tur 3 | Toplam |
|---|:---:|:---:|:---:|:---:|
| **F-C (Code Analyst)** | | | | |
| **F-A (Adversary)** | | | | |
| **F-R (Research & Verify)** | | | | |
| **CONFIRMED** | | | | |
| **REFUTED** | | | | |
| **UNVERIFIABLE** | | | | |
| **≥2 Ajan Desteği** | | | | |

**Durma Nedeni:** <Standart tamamlandı | Deep tur çalıştı>
