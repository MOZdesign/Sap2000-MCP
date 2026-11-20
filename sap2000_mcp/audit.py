"""İşlem günlüğü (kural 6.3). Her yazma ve dosya işlemi JSON satırı olarak kaydedilir."""
import json
import os
import time
from pathlib import Path

LOG_PATH = Path(os.environ.get("SAP_MCP_LOG", Path(__file__).resolve().parent.parent / "islem_gunlugu.jsonl"))


def log(action: str, **fields) -> None:
    rec = {"zaman": time.strftime("%Y-%m-%d %H:%M:%S"), "islem": action, **fields}
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except OSError:
        pass  # günlük yazılamasa da okuma işlemleri engellenmez; yazma işlemleri guard'da zaten durur
