# demarvelcdb

Ein Discord-Bot, der Karten aus dem deutschen [MarvelCDB](https://de.marvelcdb.com/) abruft und übersichtlich als Embed anzeigt.

## Features

- Kartensuche via `!de:<Kartenname>` direkt im Discord-Chat
- Bei einem Treffer: sofortige Anzeige als formatiertes Embed
- Bei mehreren Treffern (bis zu 25): interaktives Auswahlmenü
- Bei zu vielen Treffern: Hinweis mit Beispielen zur Verfeinerung
- Karten-Cache pro Bot-Session (kein wiederholtes API-Laden)

## Voraussetzungen

- Python 3.11+
- Ein Discord-Bot-Token ([Discord Developer Portal](https://discord.com/developers/applications))

## Installation

```bash
git clone https://github.com/TomBuZi/demarvelcdb.git
cd demarvelcdb
pip install -r requirements.txt
cp .env.example .env
# .env bearbeiten und DISCORD_TOKEN eintragen
```

## Starten

```bash
python bot.py
```

## Verwendung

Im Discord-Channel:

```
!de:Tigra
!de:Nick Fury
!de:Rat
```

Bei einem eindeutigen Treffer wird die Karte sofort angezeigt. Bei mehreren Treffern erscheint ein Dropdown-Menü zur Auswahl (nur für die suchende Person bedienbar, Timeout: 60 Sekunden).

## Projektstruktur

```
bot.py            # Bot-Einstiegspunkt, Karten-Cache
card_formatter.py # Embed-Formatierung für Karten
cogs/marvel.py    # Discord-Cog mit Suchlogik und UI
```

## Datenquelle

Alle Kartendaten stammen von der öffentlichen API von [de.marvelcdb.com](https://de.marvelcdb.com/api/public/cards/).
