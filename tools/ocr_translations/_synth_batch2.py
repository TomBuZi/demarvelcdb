"""Build synthezoid_encounter translations - batch 2."""
from _claude_accumulate import add_cards

cards = [
    # Young Avengers modular
    {
        "code": "57055",
        "name": "Patriot",
        "flavor": "„Wissen die nicht, dass WIR die Guten sind?\"",
        "traits": "Young Avenger.",
        "text": "Zähigkeit.\n<b>Sobald aufgedeckt</b>: Gib dem gegnerischen Anführer eine Zäh-Statuskarte.",
    },
    {
        "code": "57056",
        "name": "Hawkeye",
        "flavor": "„Zerplatz bloß nicht vor Neid, Clint!\"",
        "traits": "Young Avenger.",
        "text": "[star] Hawkeyes Angriffe erhalten Durchdringend und Fernkampf.\n<b>Sobald aufgedeckt</b>: Lege ein Upgrade unter deiner Kontrolle ab.",
    },
    {
        "code": "57057",
        "name": "Stature",
        "flavor": "„Du solltest ein Mädchen, das zwei Stockwerke hoch wachsen kann, nicht so von oben herab behandeln!\"",
        "traits": "Riesig. Young Avenger.",
        "text": "Wache.\n<b>Sobald aufgedeckt</b>: Lege einen Vorteil unter deiner Kontrolle ab.",
    },
    {
        "code": "57058",
        "name": "Teenager-Superhelden",
        "flavor": "„Young Avengers, sammeln!\" -Kate Bishop",
        "text": "<b>Sobald aufgedeckt</b>: Handle die <b>Sobald aufgedeckt</b>-Fähigkeit auf jedem Schergen im Spiel ab. Falls auf diese Weise keine <b>Sobald aufgedeckt</b>-Fähigkeit abgehandelt wurde, erhält diese Karte Nachrüsten.",
    },
    {
        "code": "57059",
        "name": "Young Avengers",
        "flavor": "Die nächste Generation von Superhelden hofft, das Erbe ihrer Vorgänger weiterführen zu können.",
        "text": "Hindernis 1[per_hero].\nDer erste Scherge, der jede Runde aufgedeckt wird, erhält Nachrüsten.",
    },
    # Scarlet Twins modular
    {
        "code": "57060",
        "name": "Speed",
        "flavor": "„Hey, ihr alten Greise! Jetzt legt mal einen Zahn zu.\"",
        "traits": "Young Avenger.",
        "text": "Erstschlag.\n<b>Sobald aufgedeckt</b>: Du wirst betäubt. Füge ansonsten deiner Identität 2 Schaden zu.",
    },
    {
        "code": "57061",
        "name": "Wiccan",
        "flavor": "„Da habt ihr euch mit den falschen Kids angelegt.\"",
        "traits": "Young Avenger.",
        "text": "Anstacheln 1.\n<b>Sobald aufgedeckt</b>: Du wirst verwirrt. Platziere ansonsten 2 Bedrohung auf dem Hauptplan.",
    },
    {
        "code": "57062",
        "name": "Supergeschwindigkeit",
        "flavor": "„Das hast du nicht kommen sehen, oder?\" -Speed",
        "text": "<b>Sobald aufgedeckt</b>: Lege 1 zufällige Karte von deiner Hand ab. Nimm indirekten Schaden in Höhe ihrer Kosten.\n<hr />\n[star] <b>Boost</b>: Lege 1 Karte von deiner Hand ab.",
    },
    {
        "code": "57063",
        "name": "Zauberkunst",
        "flavor": "„BLENDBLITZBLENDBLITZBLENDBLITZ.\" -Wiccan",
        "text": "<b>Erzwungene Unterbrechung</b>: Sobald du eine Karte spielst, hebe die Effekte der Karte auf und lege sie ab. Lege dann diese Karte ab.",
    },
    {
        "code": "57064",
        "name": "Geschwister mit Superkräften",
        "flavor": "Wiccan und Speed treten in die Fußstapfen ihrer Superhelden-Eltern: Vision und Scarlet Witch.",
        "text": "Hindernis 1[per_hero].\n<b>Sobald besiegt</b>: Der Spieler, der diesen Plan besiegt hat, legt 1 Karte von seiner Hand ab.",
    },
    # Moon Knight modular
    {
        "code": "57065",
        "name": "Moon Knight",
        "flavor": "„Du steckst jetzt mächtig in Schwierigkeiten.\"",
        "traits": "Defender. Elite.",
        "text": "Vergeltung 2. Zähigkeit.\n<b>Sobald aufgedeckt</b>: Handle die <b>Sobald aufgedeckt</b>-Fähigkeit der obersten Verratskarte im Begegnungs-Ablagestapel ab.",
    },
    {
        "code": "57066",
        "name": "Wurf-Halbmonde",
        "traits": "Waffe.",
        "text": "Hänge diese Karte an Moon Knight an. Hänge sie ansonsten an den gegnerischen Anführer an.\n[star] <b>Erzwungene Unterbrechung</b>: Sobald der Charakter mit diesem Anhang angreift, erhält der Angriff Durchdringend und Fernkampf. Lege diese Karte nach dem Angriff ab.",
    },
    {
        "code": "57067",
        "name": "Faust von Khonshu",
        "flavor": "„Ich bin die Faust von Khonshu! Ich bin die Rache!\" -Moon Knight",
        "text": "<b>Sobald aufgedeckt</b>: Erschöpfe deine Identität und füge ihr 2 Schaden zu.\n<hr />\n[star] <b>Boost</b>: Erschöpfe deine Identität.",
    },
    {
        "code": "57068",
        "name": "Khonshus Avatar",
        "text": "Hindernis 1[per_hero].\n<b>Sobald besiegt</b>: Lege Karten vom Begegnungsdeck ab, bis eine Verratskarte abgelegt wird. Handle die <b>Sobald aufgedeckt</b>-Fähigkeit der Karte ab.",
    },
    # Royal Guard modular
    {
        "code": "57069",
        "name": "Janus",
        "flavor": "„Niemand kann der Königlichen Garde von Atlantis entkommen!\"",
        "traits": "Atlantis.",
        "text": "<b>Sobald aufgedeckt</b>: Falls du das Merkmal <i>Gejagt</i> hast, wird Janus gegen dich aktiviert. Lege ansonsten die obersten 2 Karten deines Decks ab.",
    },
    {
        "code": "57070",
        "name": "Amir",
        "flavor": "„Mein Lord Namor hat befohlen, dich zu ihm zu bringen.\"",
        "traits": "Atlantis.",
        "text": "<b>Sobald aufgedeckt</b>: Falls du das Merkmal <i>Gejagt</i> hast, wird Amir gegen dich aktiviert. Lege ansonsten die obersten 2 Karten deines Decks ab.",
    },
    {
        "code": "57071",
        "name": "Atlanter",
        "text": "<b>Sobald aufgedeckt</b>: Lege die obersten 3 Karten deines Decks ab. Falls du in deiner:\n• Alter-Ego-Gestalt bist, platziere für jeden unterschiedlichen Kartentyp, der auf diese Weise abgelegt wurde, 1 Bedrohung auf dem Hauptplan.\n• Heldengestalt bist, nimm für jeden unterschiedlichen Kartentyp, der auf diese Weise abgelegt wurde, 1 indirekten Schaden.",
    },
    {
        "code": "57072",
        "name": "Blutschuld",
        "text": "Du erhältst das Merkmal <i>Gejagt</i>.\n<b>Alter Ego - Aktion</b>: Lege die obersten 8 Karten deines Decks ab → lege diese Karte ab.",
    },
    {
        "code": "57073",
        "name": "Die Königliche Garde",
        "text": "Hindernis 1[per_hero].\n<b>Sobald besiegt</b>: Das gegnerische Team durchsucht das Begegnungsdeck und den Ablagestapel nach der Verpflichtung Blutschuld und teilt sie dem Spieler, der diesen Plan besiegt hat, als verdeckte Begegnungskarte zu.",
    },
    # Standard PVP duplicates 78-81 (identical to 36-39)
    {
        "code": "57078",
        "name": "Gerechte Sache",
        "flavor": "„Ich war jahrelang Doppelagentin. Für eine gerechte Sache würde ich fast alles tun.\" -Spider-Woman",
        "text": "<b>Sobald aufgedeckt</b>: Der gegnerische Anführer treibt den Plan voran. Falls in deinem Team mehr als 1 Spieler ist, gib dem gegnerischen Anführer für diese Aktivierung eine zusätzliche Boost-Karte.",
    },
    {
        "code": "57079",
        "name": "Was immer nötig ist",
        "flavor": "„Ziel im Visier. Angriff einleiten.\" -Captain Marvel",
        "text": "<b>Sobald aufgedeckt (Alter Ego)</b>: Der gegnerische Anführer greift deinen Anführer an.\n<b>Sobald aufgedeckt (Held)</b>: Der gegnerische Anführer greift dich an.",
    },
    {
        "code": "57080",
        "name": "Gezielter Angriff",
        "text": "<b>Sobald aufgedeckt</b>: Das gegnerische Team durchsucht die obersten 5 Karten des Begegnungsdecks nach einer Karte und teilt sie dir als verdeckte Begegnungskarte zu.\n<hr />\n[star] <b>Boost</b>: Diese Karte erhält [crisis] für jeden Spieler in deinem Team.",
    },
    {
        "code": "57081a",
        "name": "Eine Seite wählen",
        "text": "Dauerhaft.\nDer gegnerische Anführer kann nicht mehr als 2 Schaden durch jeden Angriff nehmen.\n<b>Erzwungene Reaktion</b>: Nachdem die letzte Bedrohung von dieser Karte entfernt worden ist, durchsucht das gegnerische Team die obersten 5 Karten des Begegnungsdecks nach 1[per_hero] Begegnungskarte und teilt jedem Spieler eine davon als verdeckte Begegnungskarte zu. Drehe diese Karte um.",
    },
    {
        "code": "57081b",
        "name": "Jetzt wird's persönlich",
        "text": "<i>Gib diese Karte dem Startspieler.</i>\n<b>Aktion</b>: Entferne diese Karte aus dem Spiel → jeder Spieler in deinem Team wählt 2 der beiseitegelegten Spielerkarten deines Anführers und nimmt sie auf seine Hand.",
    },
]

result = add_cards(cards)
print('added:', len(result['added']))
print('skipped:', len(result['skipped']))
print('total:', result['total'])
