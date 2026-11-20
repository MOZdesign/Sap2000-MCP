"""Sahte SAP2000 modeliyle testler (SAP2000 gerekmez). Çalıştır: python -m pytest tests -q"""
import pytest
from sap2000_mcp import guard, oapi, units


class _Ns:  # basit ad alanı
    def __init__(self, **k): self.__dict__.update(k)


class FakeModel:
    def __init__(self, path="C:/m/proje.sdb"):
        self.units = 12; self.path = path; self.saved = []
        self.PointObj = _Ns(GetNameList=lambda n, a: (2, ["1", "2"], 0),
                            GetCoordCartesian=lambda nm, x, y, z, cs: (1.0, 2.0, 3.0, 0))
        self.FrameObj = _Ns(GetNameList=lambda n, a: (1, ["F1"], 0),
                            GetPoints=lambda nm, a, b: ("1", "2", 0),
                            GetSection=lambda nm, a, b: ("K40x60", "N.A.", 0))
        self.LoadPatterns = _Ns(GetNameList=lambda n, a: (2, ["G1", "Q"], 0))
        self.LoadCases = _Ns(GetNameList_1=lambda n, a, t=0: (1, ["G1"], 0))
        self.RespCombo = _Ns(GetNameList=lambda n, a: (1, ["ENV"], 0))
        self.File = _Ns(Save=self._save)
        self.Analyze = _Ns(RunAnalysis=lambda: 0)
        self.log_units = []

    def _save(self, name): self.saved.append(name); return 0
    def GetPresentUnits(self): return self.units
    def SetPresentUnits(self, u): self.log_units.append(u); self.units = u; return 0
    def GetModelFilename(self, inc=True): return self.path
    def GetModelIsLocked(self): return False
    def GetVersion(self, a, b): return ("26.0.0", 26.0, 0)


class FakeObj:
    def __init__(self, m): self.SapModel = m
    def GetOAPIVersionNumber(self): return 1.0


def mk(path="C:/m/proje.sdb"):
    return oapi.Backend(FakeObj(FakeModel(path)))


def test_unpack_hata_yutulmaz():
    with pytest.raises(oapi.OapiError):
        oapi.unpack((1, 2, 5), "X")


def test_birim_geri_yuklenir():
    b = mk(); b.points(10)
    assert b.m.units == 12 and b.m.log_units == [6, 12]


def test_okuma():
    b = mk()
    assert b.points(1)["toplam"] == 2 and b.points(1)["donen"] == 1
    assert b.frames(5)["elemanlar"][0]["kesit"] == "K40x60"
    assert b.combos() == ["ENV"]


def test_onaysiz_kayit_reddedilir():
    with pytest.raises(guard.GuardError):
        mk().save_copy("C:/m/proje_mcp_20261120.sdb", False)


def test_orijinal_ezilmez(tmp_path):
    orig = tmp_path / "p.sdb"; orig.write_text("x")
    b = mk(str(orig))
    with pytest.raises(guard.GuardError):
        b.save_copy(str(orig), True)
    assert b.m.saved == []


def test_mevcut_hedef_ezilmez(tmp_path):
    orig = tmp_path / "p.sdb"; orig.write_text("x")
    hedef = tmp_path / "p_mcp_20261120.sdb"; hedef.write_text("y")
    with pytest.raises(guard.GuardError):
        mk(str(orig)).save_copy(str(hedef), True)


def test_kopya_kaydi_ve_gunluk(tmp_path, monkeypatch):
    from sap2000_mcp import audit
    monkeypatch.setattr(audit, "LOG_PATH", tmp_path / "log.jsonl")
    orig = tmp_path / "p.sdb"; orig.write_text("x")
    b = mk(str(orig)); hedef = str(tmp_path / "p_mcp_20261120.sdb")
    b.save_copy(hedef, True)
    assert len(b.m.saved) == 1 and (tmp_path / "log.jsonl").exists()


def test_analiz_yalnizca_kopyada():
    with pytest.raises(guard.GuardError):
        mk("C:/m/proje.sdb").run_analysis(True)
    assert mk("C:/m/proje_mcp_20261120.sdb").run_analysis(True)["durum"] == "analiz tamam"
    with pytest.raises(guard.GuardError):
        mk("C:/m/proje_mcp_20261120.sdb").run_analysis(False)


def test_birimler():
    assert units.m2_to_cm2(0.24) == pytest.approx(2400)
    assert units.cm2_to_m2(2400) == pytest.approx(0.24)
    assert units.force_to_kn(1, "tf") == pytest.approx(9.80665)
    assert units.length_to_m(250, "mm") == pytest.approx(0.25)
