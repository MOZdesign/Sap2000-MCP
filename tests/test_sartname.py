"""Şartname arama: sentetik sayfalarla (gerçek PDF gerekmez)."""
import pytest
from sap2000_mcp import sartname as s

SAYFALAR = [
    "İÇİNDEKİLER\n7.4.4 Enine Donatı Koşulları ........ 144\n7.7.4 Kolonlarda Enine Donatı ........ 155",
    "7.4.4 Enine Donatı Koşulları\nKiriş mesnetlerinde kolon yüzünden itibaren kiriş yüksekliğinin iki katı kadar uzunluktaki bölge sarılma bölgesidir.\n"
    "7.4.5 Kesme Güvenliği\nKesme kuvveti hesabı.",
    "7.7.4 Enine Donatı Koşulları\nKolonlarda sarılma bölgesi boyunca etriye aralığı şu kadardır.\n7.7.4.1 Sarılma bölgeleri\nBurada aralık sınırlıdır.\n7.8 Perdeler\nPerde.",
    "",
]
B = s.Belge("TEST", SAYFALAR)


def test_norm_uzunluk_korunur():
    t = "İĞÜŞÖÇı Kolon"
    assert len(s.norm(t)) == len(t) and s.norm(t).startswith("igusoci")


def test_kelime_koku_ek_farkini_tolere_eder():
    assert "sarilm" in s._kelimeler("sarılma bölgeleri") and "bolgel" in s._kelimeler("bölgesi") or "bolges" in s._kelimeler("bölgesi")


def test_ara_turkce_karakter_ve_sayfa(monkeypatch):
    monkeypatch.setattr(s, "kayitlar", lambda: {"TEST": "x"})
    monkeypatch.setattr(s, "belge_yukle", lambda ad, yenile=False: B)
    r = s.ara("sarilma bolgesi etriye")
    assert r["sonuc_sayisi"] >= 1 and r["sonuclar"][0]["belge"] == "TEST" and r["sonuclar"][0]["sayfa"] in (2, 3)
    assert "uyari" in r
    with pytest.raises(ValueError):
        s.ara("   ")


def test_madde_getir_icindekileri_atlar_ve_sinirda_durur():
    r = B.madde_getir("7.4.4")
    assert r["bulundu"] and r["sayfa"].startswith("2") and "sarılma bölgesidir" in r["metin"] and "Kesme kuvveti hesabı" not in r["metin"]
    r2 = B.madde_getir("7.7.4")
    assert r2["bulundu"] and "7.7.4.1" in r2["metin"] and "Perde." not in r2["metin"]
    assert not B.madde_getir("9.9.9")["bulundu"]
    with pytest.raises(ValueError):
        B.madde_getir("Şekil 7.3")


def test_sayfa_getir_sinirlar_ve_metinsiz_sayfa():
    assert B.sayfa_getir(2)["sayfa"] == 2
    assert "taranmış" in B.sayfa_getir(4)["not"]
    for n in (0, 5):
        with pytest.raises(ValueError):
            B.sayfa_getir(n)


def test_okunamayan_sayfa_sessizce_yutulmaz():
    b = s.Belge("T", ["a", ""], "x", hatali=[2])
    assert "OKUNAMADI" in b.sayfa_getir(2)["not"]
