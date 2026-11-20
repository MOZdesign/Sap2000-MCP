"""SAP2000 V26 MCP sunucusu (stdio). Aşama 1: okuma araçları + kopyaya kaydet + kopyada analiz."""
from datetime import date

from mcp.server.fastmcp import FastMCP

from . import guard, oapi

mcp = FastMCP("sap2000-own")
_backend = None


def be():
    global _backend
    if _backend is None:
        _backend = oapi.Backend(oapi.connect())
    return _backend


@mcp.tool()
def model_bilgisi() -> dict:
    """Açık SAP2000 modelinin sürüm, dosya yolu ve kilit durumunu verir (salt okunur)."""
    return be().info()


@mcp.tool()
def noktalar(limit: int = 200) -> dict:
    """Düğüm noktaları ve koordinatları (m). Salt okunur."""
    return be().points(limit)


@mcp.tool()
def cubuk_elemanlar(limit: int = 200) -> dict:
    """Çubuk elemanlar: uç noktaları ve kesit adı. Salt okunur."""
    return be().frames(limit)


@mcp.tool()
def yuk_tanimlari() -> dict:
    """Yük desenleri, yük durumları ve kombinasyon adları. Salt okunur."""
    b = be()
    return {"yuk_desenleri": b.load_patterns(), "yuk_durumlari": b.load_cases(), "kombinasyonlar": b.combos()}


@mcp.tool()
def analiz_durumu() -> dict:
    """Her yük durumu için analiz durumu (1=çalışmadı, 2=çalışamadı, 3=çalışıyor, 4=bitti). Salt okunur."""
    return be().case_status()


@mcp.tool()
def mod_periyotlari(modal_durum: str) -> list:
    """Verilen modal yük durumunun periyotları (s) ve frekansları (Hz). Analiz yapılmış olmalı."""
    return be().modal_periods(modal_durum)


@mcp.tool()
def taban_reaksiyonlari(durumlar: list[str] = [], kombinasyonlar: list[str] = []) -> dict:
    """Taban reaksiyonları (kN, kNm). Hangi durum/kombinasyondan geldiği her satırda yazar."""
    return be().base_reactions(durumlar, kombinasyonlar)


@mcp.tool()
def eleman_kesit_tesirleri(eleman: str, durumlar: list[str] = [], kombinasyonlar: list[str] = []) -> list:
    """Çubuk eleman kesit tesirleri (P, V2, V3 kN; T, M2, M3 kNm)."""
    return be().frame_forces(eleman, durumlar, kombinasyonlar)


@mcp.tool()
def dugum_yerdegistirmeleri(dugum: str, durumlar: list[str] = [], kombinasyonlar: list[str] = []) -> list:
    """Düğüm yerdeğiştirmeleri (m, rad)."""
    return be().joint_displ(dugum, durumlar, kombinasyonlar)


@mcp.tool()
def kopya_oner() -> dict:
    """Açık modelin yanına yazılacak kopya adı önerir (*_mcp_YYYYMMDD.sdb). Dosya yazmaz."""
    p = be().m.GetModelFilename(True)
    return {"oneri": guard.suggest_copy_name(p, date.today().strftime("%Y%m%d"))}


@mcp.tool()
def kopya_kaydet(hedef_yol: str, onay: bool = False) -> dict:
    """YAZMA: Modeli yeni adlı kopya olarak kaydeder; orijinal ezilmez. Kullanıcı onayı olmadan onay=True verme."""
    return be().save_copy(hedef_yol, onay)


@mcp.tool()
def analiz_calistir(onay: bool = False) -> dict:
    """YAZMA: Yalnızca *_mcp_YYYYMMDD.sdb kopyasında analiz çalıştırır. Kullanıcı onayı olmadan onay=True verme."""
    return be().run_analysis(onay)


# ---- şartname / yönetmelik (salt okunur; mühendisin kendi PDF'leri yerinde okunur, SAP2000 gerekmez) ----
@mcp.tool()
def sartname_listesi() -> dict:
    """Kayıtlı şartname/yönetmelik belgeleri (TBDY2018, TS500…) ve indeks durumu. Salt okunur."""
    from . import sartname
    return sartname.liste()


@mcp.tool()
def sartname_ara(sorgu: str, belgeler: list[str] = []) -> dict:
    """Şartnamelerde arama (Türkçe, belge + sayfa + başlık atıflı en çok 8 alıntı). Bulunan değerleri atıfla göster; sayfadan doğrulat."""
    from . import sartname
    return sartname.ara(sorgu, belgeler or None)


@mcp.tool()
def sartname_madde_getir(belge: str, madde: str) -> dict:
    """Bir belgenin numaralı maddesinin metni (örn. belge='TBDY2018', madde='7.4.4'), sayfa atıflı. Madde sonu sezgiseldir."""
    from . import sartname
    return sartname.belge_yukle(belge).madde_getir(madde)


@mcp.tool()
def sartname_sayfa_getir(belge: str, sayfa: int) -> dict:
    """Bir belgenin tek sayfasının metni (1'den başlar). Tablo/formül bozuk çıkabilir: kullanıcıya sayfayı doğrulattır."""
    from . import sartname
    return sartname.belge_yukle(belge).sayfa_getir(sayfa)


def main():
    mcp.run()


if __name__ == "__main__":
    main()
