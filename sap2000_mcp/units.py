"""Birim kuralları: kN, m, cm² (kural dosyası Bölüm 3).

SAP2000 API'si kN_m_C iken alanlar m² gelir. m² -> cm² dönüşümü YALNIZCA burada yapılır.
"""
KN_M_C = 6            # eUnits.kN_m_C (SAP2000 belgesi: SetPresentUnits)
M2_TO_CM2 = 10_000.0  # 1 m² = 10 000 cm²


def m2_to_cm2(value_m2: float) -> float:
    return value_m2 * M2_TO_CM2


def cm2_to_m2(value_cm2: float) -> float:
    return value_cm2 / M2_TO_CM2


# Girdi dönüşümleri (kural 3.5): dönüşüm çağıran tarafından belirtilir.
_FORCE_TO_KN = {"kN": 1.0, "N": 1e-3, "kgf": 9.80665e-3, "tf": 9.80665}
_LENGTH_TO_M = {"m": 1.0, "cm": 1e-2, "mm": 1e-3}


def force_to_kn(value: float, unit: str) -> float:
    if unit not in _FORCE_TO_KN:
        raise ValueError(f"Desteklenmeyen kuvvet birimi: {unit}")
    return value * _FORCE_TO_KN[unit]


def length_to_m(value: float, unit: str) -> float:
    if unit not in _LENGTH_TO_M:
        raise ValueError(f"Desteklenmeyen uzunluk birimi: {unit}")
    return value * _LENGTH_TO_M[unit]
