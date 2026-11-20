"""Güvenlik katmanı (kural dosyası Bölüm 2).

- Varsayılan mod salt okunur.
- Orijinal .sdb asla ezilmez; yalnızca yeni adlı kopya yazılır.
- Yazma/kaydetme için açık onay (confirm=True) gerekir.
"""
import os
import re
from pathlib import Path


class GuardError(Exception):
    pass


def _norm(p: str) -> str:
    return os.path.normcase(os.path.abspath(p))


def require_confirm(confirm: bool, what: str) -> None:
    if confirm is not True:
        raise GuardError(f"Onay gerekli: {what}. Kullanıcıdan açık onay alındıktan sonra confirm=True ile çağır.")


def check_copy_target(original_path: str, target_path: str) -> str:
    """Kopya hedefini doğrular; geçerli ise normalize edilmiş yolu döner."""
    if not original_path:
        raise GuardError("Modelin dosya yolu yok; önce kullanıcı modeli kaydetmeli.")
    if not target_path.lower().endswith(".sdb"):
        raise GuardError("Hedef .sdb uzantılı olmalı.")
    if _norm(target_path) == _norm(original_path):
        raise GuardError("Hedef, orijinal dosyayla aynı: orijinal üzerine kaydetmek yasak.")
    if Path(target_path).exists():
        raise GuardError("Hedef dosya zaten var: mevcut dosya ezilmez.")
    if not Path(target_path).parent.exists():
        raise GuardError("Hedef klasör yok.")
    return _norm(target_path)


_COPY_NAME = re.compile(r"_mcp_\d{8}", re.IGNORECASE)


def is_mcp_copy(path: str) -> bool:
    """Analiz yalnızca MCP'nin açtığı kopyada çalıştırılır (RunAnalysis dosya yolu gerektirir ve sonuçları modele yazar)."""
    return bool(path) and bool(_COPY_NAME.search(os.path.basename(path)))


def suggest_copy_name(original_path: str, yyyymmdd: str) -> str:
    p = Path(original_path)
    return str(p.with_name(f"{p.stem}_mcp_{yyyymmdd}.sdb"))
