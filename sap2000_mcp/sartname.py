"""Şartname / yönetmelik arama (salt okunur). Mühendisin KENDİ PDF'leri yerinde okunur; kopyalanmaz, hiçbir yere yüklenmez.

- Kayıt: proje kökündeki `sartname_kutuphane.json` ({"belgeler": {"TS500": "C:\\...\\TS500.pdf", ...}}); SARTNAME_KUTUPHANE ortam değişkeniyle değiştirilebilir.
- Önbellek: `sartname_onbellek/<ad>.json` (sayfa metinleri; PDF'in boyutu/tarihi değişirse yenilenir). `python -m sap2000_mcp.sartname --indeksle` önceden kurar.
- Metin PDF'ten OTOMATİK okunur (pypdf): sayı/formül/tablo bozulmuş olabilir. Her sonuç belge + madde + sayfa taşır; değer kullanmadan önce sayfadan doğrulanmalıdır.
- Şartname sayıları uydurulmaz: bu modül yalnız PDF'teki metni bulur ve getirir.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
KUTUPHANE = Path(os.environ.get("SARTNAME_KUTUPHANE") or KOK / "sartname_kutuphane.json")
ONBELLEK = KOK / "sartname_onbellek"
UYARI = ("Metin PDF'ten otomatik okundu (sayı, formül, tablo bozulmuş olabilir). Bir değeri kullanmadan önce belge + madde + sayfa atfıyla "
         "kullanıcıya göster ve sayfadan doğrulattır; değer uydurma.")
MAKS_METIN = 6000

_TABLO = str.maketrans({"İ": "i", "I": "i", "ı": "i", "Ş": "s", "ş": "s", "Ğ": "g", "ğ": "g", "Ü": "u", "ü": "u", "Ö": "o", "ö": "o", "Ç": "c", "ç": "c"})
_BASLIK = re.compile(r"^\s*(\d+(?:\.\d+)*)\.?\s*[-–]?\s*([A-ZÇĞİÖŞÜa-zçğıöşü(\[])")


def norm(s: str) -> str:
    """Karakter-karakter eşlemeli (uzunluk korunur) küçük harf + ASCII katlama: konum, özgün metinle hizalı kalır."""
    return s.translate(_TABLO).lower()


def _kelimeler(sorgu: str) -> list[str]:
    out = []
    for k in re.findall(r"[a-z0-9]+", norm(sorgu)):
        if len(k) >= 3 or k.isdigit():
            out.append(k[:6] if not k.isdigit() else k)   # ek/çekim farkı için kök (ilk 6 harf)
    return list(dict.fromkeys(out))


class Belge:
    def __init__(self, ad: str, sayfalar: list[str], dosya: str = "", hatali: list[int] | None = None):
        self.ad = ad
        self.sayfalar = sayfalar
        self.dosya = dosya
        self.hatali = list(hatali or [])   # PDF okuyucunun metin çıkaramadığı sayfalar (1'den başlar): SESSİZCE YUTULMAZ
        self._norm = [norm(t) for t in sayfalar]

    # ---- arama ----
    def sayfa_puani(self, kelimeler: list[str], tam_ifade: str, df: dict[str, int], n_toplam: int) -> list[tuple[float, int, int]]:
        sonuc = []
        for i, nt in enumerate(self._norm):
            puan, ilk = 0.0, -1
            for k in kelimeler:
                tf = len(re.findall(r"(?<![a-z0-9])" + re.escape(k), nt))
                if tf:
                    idf = math.log(1 + n_toplam / (1 + df.get(k, 0)))
                    puan += idf * (1 + math.log(1 + tf))
                    m = re.search(r"(?<![a-z0-9])" + re.escape(k), nt)
                    if m and (ilk < 0 or m.start() < ilk):
                        ilk = m.start()
            if puan and len(kelimeler) > 1 and tam_ifade and tam_ifade in nt:
                puan *= 1.6
                ilk = nt.find(tam_ifade)
            if puan:
                sonuc.append((puan, i, ilk))
        return sonuc

    def baslik_bul(self, sayfa_idx: int, konum: int) -> str:
        """Eşleşmeden ÖNCEKİ en yakın numaralı başlık (sayfada yoksa önceki sayfalara bakar); sezgisel."""
        for p in range(sayfa_idx, max(-1, sayfa_idx - 4), -1):
            metin = self.sayfalar[p] if p != sayfa_idx else self.sayfalar[p][: max(konum, 0) + 1]
            for satir in reversed(metin.splitlines()):
                m = _BASLIK.match(satir)
                if m and len(satir.strip()) < 140 and "...." not in satir:
                    return satir.strip()[:120]
        return ""

    # ---- madde ----
    def madde_getir(self, madde: str) -> dict:
        madde = madde.strip().rstrip(".")
        if not re.fullmatch(r"\d+(?:\.\d+)*", madde):
            raise ValueError("madde '7.4.4' gibi numara olmalı (şekil/çizelge numaraları için sartname_ara kullan)")
        derinlik = madde.count(".")
        adaylar = []
        for p, metin in enumerate(self.sayfalar):
            satirlar = metin.splitlines()
            for li, satir in enumerate(satirlar):
                m = _BASLIK.match(satir)
                if not m or m.group(1) != madde or "...." in satir:
                    continue
                govde = [satir.strip()]
                bitis_p = p
                durdu = False
                for p2 in range(p, min(len(self.sayfalar), p + 6)):
                    kaynak = satirlar[li + 1:] if p2 == p else self.sayfalar[p2].splitlines()
                    for s2 in kaynak:
                        m2 = _BASLIK.match(s2)
                        if m2 and "...." not in s2 and len(s2.strip()) < 140:
                            n2 = m2.group(1)
                            if not n2.startswith(madde + ".") and n2 != madde and n2.count(".") <= max(derinlik, 1):
                                durdu = True
                                break
                        govde.append(s2.rstrip())
                    bitis_p = p2
                    if durdu or sum(len(x) for x in govde) > MAKS_METIN:
                        break
                adaylar.append((sum(len(x) for x in govde), p, bitis_p, "\n".join(govde)))
        if not adaylar:
            return {"bulundu": False, "belge": self.ad, "madde": madde, "mesaj": "Bu numaralı başlık bulunamadı (başlık biçimi PDF'te farklı olabilir): sartname_ara ile arayın."}
        # İçindekiler satırları kısa kalır: en uzun gövdeli adayı al
        uzun, p, bitis_p, metin = max(adaylar, key=lambda a: a[0])
        kesildi = len(metin) > MAKS_METIN
        return {"bulundu": True, "belge": self.ad, "madde": madde, "sayfa": f"{p + 1}" + (f"-{bitis_p + 1}" if bitis_p != p else ""),
                "metin": metin[:MAKS_METIN], "kesildi": kesildi,
                "not": "Madde sonu sezgisel bulundu; sayfa sınırlarını PDF'ten doğrulatın.", "uyari": UYARI}

    def sayfa_getir(self, sayfa: int) -> dict:
        if not (1 <= sayfa <= len(self.sayfalar)):
            raise ValueError(f"sayfa 1–{len(self.sayfalar)} arasında olmalı")
        t = self.sayfalar[sayfa - 1]
        out = {"belge": self.ad, "sayfa": sayfa, "toplam_sayfa": len(self.sayfalar), "metin": t[:MAKS_METIN], "kesildi": len(t) > MAKS_METIN, "uyari": UYARI}
        if sayfa in self.hatali:
            out["not"] = "Bu sayfa PDF okuyucuyla OKUNAMADI (hata): PDF'ten elle bakılmalı."
        elif not t.strip():
            out["not"] = "Bu sayfada metin yok (taranmış görüntü olabilir): PDF'ten elle bakılmalı."
        return out


# ---------------------------------------------------------------------------------------------------------
def kayitlar() -> dict[str, str]:
    if not KUTUPHANE.exists():
        raise FileNotFoundError(f"Şartname kayıt dosyası yok: {KUTUPHANE}")
    return dict(json.loads(KUTUPHANE.read_text(encoding="utf-8")).get("belgeler", {}))


def _pdf_oku(yol: str) -> tuple[list[str], list[int]]:
    """Dönüş: (sayfa metinleri, okunamayan sayfa numaraları). Tek sayfa bozuksa belge düşmez ama sayfa İŞARETLENİR."""
    from pypdf import PdfReader  # gecikmeli: yalnız PDF gerektiğinde
    r = PdfReader(yol)
    out, hatali = [], []
    for i, p in enumerate(r.pages):
        try:
            out.append(p.extract_text() or "")
        except Exception:
            out.append("")
            hatali.append(i + 1)
    return out, hatali


_bellek: dict[str, Belge] = {}


def belge_yukle(ad: str, yenile: bool = False) -> Belge:
    k = kayitlar()
    if ad not in k:
        raise KeyError(f"Kayıtlı şartname yok: {ad} (kayıtlılar: {', '.join(k)})")
    yol = k[ad]
    st = os.stat(yol)  # yoksa FileNotFoundError: sessiz yutulmaz
    onb = ONBELLEK / f"{ad}.json"
    if not yenile and ad in _bellek and _bellek[ad].dosya == yol:
        return _bellek[ad]
    sayfalar, hatali = None, []
    if onb.exists() and not yenile:
        try:
            d = json.loads(onb.read_text(encoding="utf-8"))
            if d.get("dosya") == yol and d.get("boyut") == st.st_size and d.get("mtime") == int(st.st_mtime):
                sayfalar, hatali = d["sayfalar"], d.get("hatali", [])
        except (ValueError, KeyError):
            sayfalar = None
    if sayfalar is None:
        sayfalar, hatali = _pdf_oku(yol)
        ONBELLEK.mkdir(exist_ok=True)
        onb.write_text(json.dumps({"dosya": yol, "boyut": st.st_size, "mtime": int(st.st_mtime), "sayfalar": sayfalar, "hatali": hatali}, ensure_ascii=False), encoding="utf-8")
    b = Belge(ad, sayfalar, yol, hatali)
    _bellek[ad] = b
    return b


def liste() -> dict:
    out = []
    for ad, yol in kayitlar().items():
        d = {"ad": ad, "dosya": yol, "var": os.path.exists(yol)}
        onb = ONBELLEK / f"{ad}.json"
        if onb.exists():
            try:
                j = json.loads(onb.read_text(encoding="utf-8"))
                s = j["sayfalar"]
                d["indeksli_sayfa"] = len(s)
                d["metinsiz_sayfa"] = sum(1 for t in s if not t.strip())
                d["okunamayan_sayfalar"] = j.get("hatali", [])
            except (ValueError, KeyError):
                pass
        out.append(d)
    return {"belgeler": out, "uyari": UYARI}


def ara(sorgu: str, belgeler: list[str] | None = None, en_cok: int = 8) -> dict:
    sorgu = (sorgu or "").strip()
    kelimeler = _kelimeler(sorgu)
    if not kelimeler:
        raise ValueError("sorgu en az bir anlamlı kelime içermeli")
    adlar = belgeler or list(kayitlar())
    yuklu = [belge_yukle(a) for a in adlar]
    n_toplam = sum(len(b.sayfalar) for b in yuklu)
    df = {k: sum(1 for b in yuklu for nt in b._norm if re.search(r"(?<![a-z0-9])" + re.escape(k), nt)) for k in kelimeler}
    tam = " ".join(re.findall(r"[a-z0-9]+", norm(sorgu)))
    tum = []
    for b in yuklu:
        for puan, i, ilk in b.sayfa_puani(kelimeler, tam, df, n_toplam):
            tum.append((puan, b, i, ilk))
    tum.sort(key=lambda x: -x[0])
    out = []
    for puan, b, i, ilk in tum[:en_cok]:
        t = b.sayfalar[i]
        bas = max(0, ilk - 160)
        out.append({"belge": b.ad, "sayfa": i + 1, "baslik": b.baslik_bul(i, ilk), "puan": round(puan, 2),
                    "alinti": re.sub(r"\s+", " ", t[bas: bas + 420]).strip()})
    return {"sorgu": sorgu, "aranan_kokler": kelimeler, "sonuc_sayisi": len(out), "sonuclar": out,
            "sonraki_adim": "sartname_madde_getir (başlık numarasıyla) ya da sartname_sayfa_getir ile tam metni al.", "uyari": UYARI}


def _indeksle():
    for ad in kayitlar():
        b = belge_yukle(ad, yenile=True)
        bos = sum(1 for t in b.sayfalar if not t.strip())
        print(f"{ad}: {len(b.sayfalar)} sayfa, {bos} metinsiz, okunamayan: {b.hatali or 'yok'}")


if __name__ == "__main__":
    if "--indeksle" in sys.argv:
        _indeksle()
    else:
        print("kullanım: python -m sap2000_mcp.sartname --indeksle")
