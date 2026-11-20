# sap2000-own — SAP2000 V26 için kendi MCP sunucumuz

Aşama 1: okuma araçları + kopyaya kaydet + yalnızca kopyada analiz. FAST'a bağımlılık yok; CSI'ın resmi OAPI'si (COM) kullanılır.

## Kurulum (64-bit Python 3.11)
    cd C:\sap2000-mcp
    python -m venv .venv
    .venv\Scripts\pip install -r requirements.txt pytest
    .venv\Scripts\python -m pytest tests -q          # sahte modelle test, SAP2000 gerekmez
    .venv\Scripts\python tests\canli_deneme.py       # SAP2000 açıkken, yalnızca okur

## Claude Code'a kayıt
    claude mcp add sap2000-own -- C:\sap2000-mcp\.venv\Scripts\python.exe -m sap2000_mcp
(Komutu `C:\sap2000-mcp` klasöründen çalıştır.)

## Güvenlik
- Çalışan SAP2000'e bağlanır, yeni örnek başlatmaz.
- Varsayılan salt okunur. `kopya_kaydet` ve `analiz_calistir` açık onay (onay=True) ister.
- Orijinal .sdb ezilmez; mevcut dosya ezilmez; analiz yalnızca `*_mcp_YYYYMMDD.sdb` kopyasında.
- Her yazma `islem_gunlugu.jsonl` dosyasına yazılır.
- Her okumada birim kN_m_C ayarlanır, sonra eski birim geri yüklenir.

## Şartname / yönetmelik araçları (salt okunur)
`sartname_listesi`, `sartname_ara`, `sartname_madde_getir`, `sartname_sayfa_getir`: mühendisin KENDİ PDF'leri yerinde okunur (kopyalanmaz, yüklenmez; SAP2000 açık olmasa da çalışır).
- Kayıt: `sartname_kutuphane.json` (ad → PDF yolu; şu an TBDY2018, TS500, TS_498, TS_708, TSEN1991_1_3). Yeni belge eklemek için bu dosyaya satır ekle.
- Önbellek: `sartname_onbellek/` (sayfa metinleri; PDF değişirse yenilenir). Önceden kurmak: `.venv\Scripts\python -m sap2000_mcp.sartname --indeksle` (~45 sn).
- Metin PDF'ten otomatik okunur (pypdf 5.9; 6.x bu PDF'lerde font hatası veriyor, bu yüzden sürüm sabit): sayı/formül/tablo bozuk olabilir. Her sonuç belge + madde + sayfa taşır; değer kullanmadan önce sayfadan doğrulanmalı.
- Metinsiz/okunamayan sayfalar `sartname_listesi` ve `sartname_sayfa_getir` çıktısında işaretlenir (TS500 ve TSEN1991-1-3'te birer sayfa metinsiz).
