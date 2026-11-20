"""CANLI deneme (SAP2000 açık, model yüklü): SADECE OKUR. python tests/canli_deneme.py
comtypes'ın ref/out parametreleri nasıl döndürdüğünü doğrular."""
import json, sys
sys.path.insert(0, ".")
from sap2000_mcp import oapi

b = oapi.Backend(oapi.connect())
print(json.dumps(b.info(), ensure_ascii=False, indent=2))
print("yuk desenleri:", b.load_patterns())
print("nokta (ilk 3):", json.dumps(b.points(3), ensure_ascii=False))
print("eleman (ilk 3):", json.dumps(b.frames(3), ensure_ascii=False))
