# MMM-Stromdata

MagicMirror²-modul som viser spotpris, strømforbruk og beregnet
spotkostnad time for time for de siste syv dagene.

## Installer på Raspberry Pi

```bash
cd ~/MagicMirror/modules
git clone https://github.com/henrikremmen/stromdata.git MMM-Stromdata
cd MMM-Stromdata
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Fyll deretter inn Agva-verdiene i `.env`:

```env
AGVA_TOKEN="..."
CUSTOMER_ID="..."
DELIVERY_POINT_ID="..."
PRICE_AREA="NO3"
```

Beskytt filen:

```bash
chmod 600 .env
```

Test generering av grafen:

```bash
.venv/bin/python plots.py
```

Grafen lagres i `public/stromdata.png`.

## MagicMirror-konfigurasjon

Legg modulen inn i `modules`-listen i `~/MagicMirror/config/config.js`:

```javascript
{
  module: "MMM-Stromdata",
  position: "middle_center",
  config: {
    width: 1000,
    updateAtMinute: 2,
    pythonPath: ".venv/bin/python",
  },
},
```

Modulen lager en graf ved oppstart og deretter to minutter etter hvert
timeskifte. `updateAtMinute` kan settes til et annet minutt fra 0 til 59.

Start MagicMirror på nytt etter at konfigurasjonen er endret.

## Oppdater modulen

```bash
cd ~/MagicMirror/modules/MMM-Stromdata
git pull
.venv/bin/python -m pip install -r requirements.txt
```

Start deretter MagicMirror på nytt.

## Viktig

- `.env` ignoreres av Git og skal ikke pushes til GitHub.
- Kostnaden er forbruk multiplisert med spotpris inkludert 25 prosent mva.
- Nettleie, leverandørpåslag og månedsavgift er ikke inkludert.
- Et utløpt Agva-token må fornyes i `.env`.
