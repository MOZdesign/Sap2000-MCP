"""SAP2000 V26 OAPI bağlantı katmanı (COM, comtypes).

İmzalar V26 CSI_OAPI_Documentation.chm'den doğrulandı. comtypes'ın ref/out parametreleri
nasıl döndürdüğü canlı SAP2000 ile ilk çalıştırmada doğrulanmalıdır (tests/canli_deneme.py).
"""
from contextlib import contextmanager
from typing import Any

from . import audit, guard
from .units import KN_M_C

PROG_ID = "CSI.SAP2000.API.SapObject"


class OapiError(Exception):
    pass


def unpack(result: Any, name: str):
    """comtypes çağrı sonucunu (…değerler, ret) ayırır; ret != 0 ise hata verir. Sessizce yutmaz (kural 4.4)."""
    if isinstance(result, (list, tuple)):
        *vals, ret = result
    else:
        vals, ret = [], result
    if ret != 0:
        raise OapiError(f"{name} başarısız, dönüş kodu={ret}")
    return vals


def connect():
    """Çalışan SAP2000 örneğine bağlanır. Yeni örnek BAŞLATMAZ (kural 2.7)."""
    import comtypes.client  # yalnızca Windows'ta
    helper = comtypes.client.CreateObject("SAP2000v1.Helper")
    helper = helper.QueryInterface(comtypes.gen.SAP2000v1.cHelper)
    try:
        sap_object = helper.GetObject(PROG_ID)
    except (OSError, comtypes.COMError) as e:
        raise OapiError("Çalışan bir SAP2000 örneği bulunamadı. Önce SAP2000'i ve modeli aç.") from e
    if sap_object is None:
        raise OapiError("Çalışan bir SAP2000 örneği bulunamadı. Önce SAP2000'i ve modeli aç.")
    return sap_object


class Backend:
    def __init__(self, sap_object):
        self.obj = sap_object
        self.m = sap_object.SapModel

    # ---- birim sarmalayıcı (kural 3.3) ----
    @contextmanager
    def kn_m(self):
        prev = self.m.GetPresentUnits()
        if self.m.SetPresentUnits(KN_M_C) != 0:
            raise OapiError("Birim kN_m_C ayarlanamadı")
        try:
            yield
        finally:
            self.m.SetPresentUnits(prev)

    # ---- genel ----
    def info(self) -> dict:
        ver = unpack(self.m.GetVersion("", 0.0), "GetVersion")
        return {
            "program_surumu": ver[0],
            "api_surumu": self.obj.GetOAPIVersionNumber(),
            "dosya": self.m.GetModelFilename(True),
            "kilitli": bool(self.m.GetModelIsLocked()),
        }

    def _names(self, fn, label):
        n, names = unpack(fn(0, []), label)
        return list(names or [])[: int(n)]

    # ---- okuma ----
    def points(self, limit):
        names = self._names(self.m.PointObj.GetNameList, "PointObj.GetNameList")
        out = []
        with self.kn_m():
            for nm in names[:limit]:
                x, y, z = unpack(self.m.PointObj.GetCoordCartesian(nm, 0.0, 0.0, 0.0, "Global"), "GetCoordCartesian")
                out.append({"ad": nm, "x_m": x, "y_m": y, "z_m": z})
        return {"toplam": len(names), "donen": len(out), "noktalar": out}

    def frames(self, limit):
        names = self._names(self.m.FrameObj.GetNameList, "FrameObj.GetNameList")
        out = []
        for nm in names[:limit]:
            p1, p2 = unpack(self.m.FrameObj.GetPoints(nm, "", ""), "FrameObj.GetPoints")
            sec, _auto = unpack(self.m.FrameObj.GetSection(nm, "", ""), "FrameObj.GetSection")
            out.append({"ad": nm, "nokta_i": p1, "nokta_j": p2, "kesit": sec})
        return {"toplam": len(names), "donen": len(out), "elemanlar": out}

    def load_patterns(self):
        return self._names(self.m.LoadPatterns.GetNameList, "LoadPatterns.GetNameList")

    def load_cases(self):
        return self._names(self.m.LoadCases.GetNameList_1, "LoadCases.GetNameList_1")

    def combos(self):
        return self._names(self.m.RespCombo.GetNameList, "RespCombo.GetNameList")

    def case_status(self):
        n, names, status = unpack(self.m.Analyze.GetCaseStatus(0, [], []), "Analyze.GetCaseStatus")
        return {nm: int(s) for nm, s in zip(list(names)[: int(n)], list(status)[: int(n)])}  # 1=çalışmadı 2=çalışamadı 3=çalışıyor 4=bitti

    # ---- sonuçlar (yalnızca seçili durum/kombinasyon, kN-m) ----
    def _select(self, cases, combos):
        unpack([self.m.Results.Setup.DeselectAllCasesAndCombosForOutput()], "DeselectAll")
        for c in cases or []:
            unpack([self.m.Results.Setup.SetCaseSelectedForOutput(c, True)], f"SetCaseSelectedForOutput({c})")
        for c in combos or []:
            unpack([self.m.Results.Setup.SetComboSelectedForOutput(c, True)], f"SetComboSelectedForOutput({c})")

    def modal_periods(self, case):
        with self.kn_m():
            self._select([case], [])
            r = unpack(self.m.Results.ModalPeriod(0, [], [], [], [], [], [], []), "Results.ModalPeriod")
        n, lc, _st, num, period, freq = r[0], r[1], r[2], r[3], r[4], r[5]
        return [{"durum": lc[i], "mod": int(num[i]), "periyot_s": period[i], "frekans_Hz": freq[i]} for i in range(int(n))]

    def base_reactions(self, cases, combos):
        with self.kn_m():
            self._select(cases, combos)
            r = unpack(self.m.Results.BaseReact(0, [], [], [], [], [], [], [], [], [], 0.0, 0.0, 0.0), "Results.BaseReact")
        n, lc, st, num, fx, fy, fz, mx, my, mz, gx, gy, gz = r
        rows = [{"durum": lc[i], "adim": st[i], "Fx_kN": fx[i], "Fy_kN": fy[i], "Fz_kN": fz[i],
                 "Mx_kNm": mx[i], "My_kNm": my[i], "Mz_kNm": mz[i]} for i in range(int(n))]
        return {"referans_nokta_m": [gx, gy, gz], "sonuclar": rows}

    def frame_forces(self, frame, cases, combos):
        with self.kn_m():
            self._select(cases, combos)
            r = unpack(self.m.Results.FrameForce(frame, 0, 0, [], [], [], [], [], [], [], [], [], [], [], [], []), "Results.FrameForce")
        n, obj, objsta, _elm, _elmsta, lc, st, _num, p, v2, v3, t, m2, m3 = r
        return [{"durum": lc[i], "adim": st[i], "mesafe_m": objsta[i], "P_kN": p[i], "V2_kN": v2[i], "V3_kN": v3[i],
                 "T_kNm": t[i], "M2_kNm": m2[i], "M3_kNm": m3[i]} for i in range(int(n))]

    def joint_displ(self, point, cases, combos):
        with self.kn_m():
            self._select(cases, combos)
            r = unpack(self.m.Results.JointDispl(point, 0, 0, [], [], [], [], [], [], [], [], [], [], []), "Results.JointDispl")
        n, _obj, _elm, lc, st, _num, u1, u2, u3, r1, r2, r3 = r
        return [{"durum": lc[i], "adim": st[i], "U1_m": u1[i], "U2_m": u2[i], "U3_m": u3[i],
                 "R1_rad": r1[i], "R2_rad": r2[i], "R3_rad": r3[i]} for i in range(int(n))]

    # ---- yazma (yalnızca kopya) ----
    def save_copy(self, target: str, confirm: bool):
        guard.require_confirm(confirm, "orijinal dosyaya dokunmadan modelin kopyasını kaydetme")
        original = self.m.GetModelFilename(True)
        tgt = guard.check_copy_target(original, target)
        # DİKKAT: File.Save(yeniAd) SAP2000'de "Farklı Kaydet" gibi çalışır; açık model bundan sonra kopyadır.
        unpack([self.m.File.Save(tgt)], "File.Save")
        audit.log("save_copy", orijinal=original, kopya=tgt)
        return {"orijinal": original, "kopya": tgt, "not": "Açık model artık kopyadır; orijinal dosya değişmedi."}

    def run_analysis(self, confirm: bool):
        guard.require_confirm(confirm, "analiz çalıştırma (mevcut sonuçlar silinebilir, model dosyası güncellenir)")
        path = self.m.GetModelFilename(True)
        if not guard.is_mcp_copy(path):
            raise guard.GuardError("Analiz yalnızca *_mcp_YYYYMMDD.sdb kopyasında çalışır. Önce save_copy kullan.")
        unpack([self.m.Analyze.RunAnalysis()], "Analyze.RunAnalysis")
        audit.log("run_analysis", dosya=path)
        return {"dosya": path, "durum": "analiz tamam"}
