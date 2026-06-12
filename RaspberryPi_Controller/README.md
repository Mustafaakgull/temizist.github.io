# TemizIST Raspberry Pi Controller

**Tek fiziksel kutu** — DB'de iki bin (`1_plastic`, `1_paper`), **tek Pi**, `machine_id: 1`.

Pi'ye aktarma: **[PI_DEPLOY.md](PI_DEPLOY.md)**

## Akış özeti

| QR | Session | Sensör | Sonra |
|----|---------|--------|--------|
| `1_plastic` | `waste_type=plastic` | GPIO 27/22 | detect → 360° → geçiş sayacı |
| `1_paper` | `waste_type=paper` | GPIO 23/24 | detect → tartı → kapak 90° |
| Yok | idle | **kapalı** | — |

Oturum sonu: mobil uygulama.

## Hızlı kurulum (Pi)

```bash
chmod +x install_pi.sh && ./install_pi.sh
source venv/bin/activate && python3 main.py
```
