"""Build synthezoid_encounter translations."""
from _claude_accumulate import add_cards

cards = [
    # She-Hulk leader I-IV
    {
        "code": "57001",
        "name": "She-Hulk",
        "traits": "Avenger. Gamma.",
        "text": "<b>Spielaufbau</b>: Das gegnerische Team findet ein Exemplar des Anhangs Übermenschliche Stärke und hängt ihn an She-Hulk an.\n<b>Erzwungene Reaktion</b>: Nachdem ein Alter Ego in seine Heldengestalt gewechselt ist, füge dem Helden 1 Schaden zu.",
    },
    {
        "code": "57002",
        "name": "She-Hulk",
        "traits": "Avenger. Gamma.",
        "text": "Standhaft.\n<b>Sobald aufgedeckt</b>: Teile jedem Spieler eine Begegnungskarte zu. She-Hulk kann in dieser Phase keinen Schaden nehmen.\n<b>Erzwungene Reaktion</b>: Nachdem ein Alter Ego in seine Heldengestalt gewechselt ist, füge dem Helden 1 Schaden zu.",
    },
    {
        "code": "57003",
        "name": "She-Hulk",
        "traits": "Avenger. Gamma.",
        "text": "<b>Spielaufbau</b>: Das gegnerische Team findet ein Exemplar des Anhangs Übermenschliche Stärke und hängt ihn an She-Hulk an.\n<b>Erzwungene Reaktion</b>: Nachdem ein Alter Ego in seine Heldengestalt gewechselt ist, füge dem Helden 1 Schaden zu.",
    },
    {
        "code": "57004",
        "name": "She-Hulk",
        "traits": "Avenger. Gamma.",
        "text": "Standhaft.\n<b>Sobald aufgedeckt</b>: Teile jedem Spieler eine Begegnungskarte zu. She-Hulk kann in dieser Phase keinen Schaden nehmen.\n<b>Erzwungene Reaktion</b>: Nachdem ein Alter Ego in seine Heldengestalt gewechselt ist, füge dem Helden 1 Schaden zu.",
    },
    # Main schemes Registration
    {
        "code": "57005a",
        "name": "Superhelden-Registrierungsgesetz",
        "text": "<b>Inhalt</b>: Gewählter Anführer (I) und (II) <i>(stattdessen (III) und (IV) im Expertenmodus)</i>. Set des gewählten Anführers, Standard-Begegnungsset und 3-4 modulare Sets.\n<b>Spielaufbau</b>: Im kompetitiven Modus findet das gegnerische Team den Nebenplan Eine Seite wählen und dein Team deckt ihn auf. Finde im kooperativen Modus den Nebenplan des gewählten Anführers und decke ihn auf.",
    },
    {
        "code": "57005b",
        "name": "Das Recht durchsetzen",
        "flavor": "„All das könnte vermieden werden, wenn ihr euch an das Gesetz halten würdet!\" -She-Hulk",
        "text": "Falls in deinem Team mehr als 1 Spieler ist, erhält dieser Abschnitt Hindernis 2[per_hero].\nDer gegnerische Anführer erhält Standhaft.",
    },
    {
        "code": "57006a",
        "name": "Pro-Registrierung-Taktiken",
        "flavor": "Iron Man und seine Avengers haben den Befehl, alle Personen mit Superkräften festzunehmen, die eine Registrierung bei S.H.I.E.L.D. verweigern. Zu diesen gehören auch ehemalige Teamkollegen wie Captain America und Spider-Woman.",
    },
    {
        "code": "57006b",
        "name": "Mighty Avengers",
        "flavor": "Iron Mans Avengers glauben so fest an die Superheldenreform, dass sie die Speerspitze im Kampf gegen ihre ehemaligen Teamkollegen bilden.",
        "text": "Solange der gegnerische Anführer angreift, bekommt er +1 ANG (+2 ANG stattdessen, falls der Angriff unverteidigt ist).\n<b>Falls dieser Abschnitt vollendet ist, verlieren die Spieler das Spiel.</b>",
    },
    # She-Hulk leader attachments + treacheries + side scheme
    {
        "code": "57007",
        "name": "Übermenschliche Stärke",
        "traits": "Superkraft.",
        "text": "Hänge diese Karte an She-Hulk an.\n[star] <b>Erzwungene Unterbrechung</b>: Sobald She-Hulk angreift, erhält dieser Angriff Overkill. Lege diese Karte nach dem Angriff ab.\n<hr />\n[star] <b>Boost</b>: Decke diese Karte auf.",
    },
    {
        "code": "57008",
        "name": "Fokussierte Wut",
        "traits": "Superkraft.",
        "text": "Hänge diese Karte an She-Hulk an.\nShe-Hulk erhält Gestählt.\n[star] <b>Erzwungene Reaktion</b>: Nachdem She-Hulk den Plan vorangetrieben hat, lege diese Karte ab.\n<hr />\n[star] <b>Boost</b>: Decke diese Karte auf.",
    },
    {
        "code": "57009",
        "name": "Links-rechts-Kombination",
        "flavor": "„Mach es nicht schwerer, als es schon ist!\" -She-Hulk",
        "text": "<b>Sobald aufgedeckt (Alter Ego)</b>: She-Hulk treibt den Plan voran. Gib ihr eine Zäh-Statuskarte.\n<b>Sobald aufgedeckt (Held)</b>: She-Hulk greift dich an. Gib ihr eine Zäh-Statuskarte.",
    },
    {
        "code": "57010",
        "name": "Bodenstampfer",
        "text": "<b>Sobald aufgedeckt</b>: Erschöpfe jeden Charakter unter deiner Kontrolle. Falls auf diese Weise kein Charakter erschöpft wurde, erhält diese Karte Nachrüsten.\n<hr />\n[star] <b>Boost</b>: Erschöpfe einen Charakter unter deiner Kontrolle.",
    },
    {
        "code": "57011",
        "name": "Gamma-Schlag",
        "flavor": "„Du hast dich mit der falschen Frau angelegt!\" -She-Hulk",
        "text": "<b>Sobald aufgedeckt</b>: Lege den Verbündeten oder Vorteil mit den höchsten Kosten unter deiner Kontrolle ab. Platziere Bedrohung in Höhe der Kosten jener Karte auf dem Hauptplan. Falls auf diese Weise keine Bedrohung auf dem Hauptplan platziert wurde, erhält diese Karte Nachrüsten.",
    },
    {
        "code": "57012",
        "name": "Juristerei",
        "text": "Helden oder Verbündete können von diesem Plan keine Bedrohung entfernen.\n<b>Alter Ego - Reaktion</b>: Nachdem du die Gestalt gewechselt hast, erschöpfe deine Identität → entferne 3 Bedrohung von diesem Plan.",
    },
    # S.H.I.E.L.D. Ops modular
    {
        "code": "57013",
        "name": "S.H.I.E.L.D.-Operator",
        "flavor": "„Unregistrierter Super an der Kreuzung 43. und Madison. Einheit 12 zum Abfangen entsenden.\"",
        "traits": "S.H.I.E.L.D.",
        "text": "Patrouille.\n<b>Sobald aufgedeckt</b>: Platziere 2 Bedrohung auf dem Hauptplan.",
    },
    {
        "code": "57014",
        "name": "Strategische Überwachung",
        "flavor": "„Ich wusste, dass wir diesem Kerl nicht trauen können.\" -Maria Hill",
        "text": "<b>Sobald aufgedeckt</b>: Gib dem gegnerischen Anführer und jedem Schergen eine Zäh-Statuskarte.\n<hr />\n[star] <b>Boost</b>: Gib dem aktivierten Gegner eine Zäh-Statuskarte.",
    },
    {
        "code": "57015",
        "name": "Schnelles Eingreifen",
        "text": "<b>Sobald aufgedeckt</b>: Lege Karten vom Begegnungsdeck ab, bis ein Scherge abgelegt wird. Falls du in deiner:\n• Alter-Ego-Gestalt bist, platziere Bedrohung in Höhe des PLA-Wertes des Schergen auf dem Hauptplan.\n• Heldengestalt bist, füge deinem Helden Schaden in Höhe des ANG-Wertes des Schergen zu.",
    },
    {
        "code": "57016",
        "name": "Mobilisierung des Heimatschutzes",
        "flavor": "„In dieser Gegend wurde der illegale Einsatz von Superkräften gemeldet. Bitte gehen Sie in Ihre Häuser und suchen Sie Schutz!\" -S.H.I.E.L.D.-Offizier",
        "text": "Hindernis 1[per_hero].\nDer erste Scherge, der in jeder Runde aufgedeckt wird, erhält Nachrüsten.",
    },
    # Thunderbolts modular
    {
        "code": "57017",
        "name": "Atlas",
        "flavor": "„Ich werde dir Schmerz beibringen, kleiner Wurm.\"",
        "traits": "Riesig. Thunderbolt.",
        "text": "<b>Sobald aufgedeckt</b>: Betäube deinen Anführer. Ansonsten wirst du betäubt.\n<hr />\n[star] <b>Boost</b>: Betäube deinen Anführer. Ansonsten wirst du betäubt.",
    },
    {
        "code": "57018",
        "name": "Songbird",
        "flavor": "„Das hat besser funktioniert, als ich dachte.\"",
        "traits": "Fliegend. Thunderbolt.",
        "text": "<b>Sobald aufgedeckt</b>: Verwirre deinen Anführer. Ansonsten wirst du verwirrt.\n<hr />\n[star] <b>Boost</b>: Verwirre deinen Anführer. Ansonsten wirst du verwirrt.",
    },
    {
        "code": "57019",
        "name": "Penance",
        "traits": "Thunderbolt.",
        "text": "<b>Sobald aufgedeckt</b>: Füge deinem Anführer 2 Schaden zu. Füge ansonsten einem Charakter unter deiner Kontrolle 2 Schaden zu.\n<hr />\n[star] <b>Boost</b>: Füge deinem Anführer 2 Schaden zu. Füge ansonsten einem Charakter unter deiner Kontrolle 1 Schaden zu.",
    },
    {
        "code": "57020",
        "name": "Blitzschnelle Gerechtigkeit",
        "flavor": "„Wir sind alle schuldig. Hier kommt die Gerechtigkeit!\" -Penance",
        "text": "<b>Sobald aufgedeckt</b>: Jeder Scherge wird gegen den Spieler aktiviert, mit dem er im Kampf ist. Ansonsten wird der gegnerische Anführer gegen dich aktiviert. Gib ihm für diese Aktivierung keine Boost-Karte.",
    },
    {
        "code": "57021",
        "name": "Die Thunderbolts",
        "flavor": "Die Regierung stellte Superverbrecher vor die Wahl: im Gefängnis verrotten oder Mitglied der Thunderbolts werden.",
        "text": "Hindernis 1[per_hero].\nSolange ein <i>Thunderbolt</i>-Scherge im Spiel ist, kann von diesem Plan keine Bedrohung entfernt werden.",
    },
    # Taskmaster modular
    {
        "code": "57022",
        "name": "Taskmaster",
        "flavor": "„Das werde ich S.H.I.E.L.D. gesondert in Rechnung stellen!\"",
        "traits": "Elite. Thunderbolt.",
        "text": "Schurkisch. Vergeltung 1. Zähigkeit.\n<b>Sobald aufgedeckt</b>: Taskmaster wird gegen dich aktiviert.",
    },
    {
        "code": "57023",
        "name": "Taskmasters Schwert",
        "traits": "Waffe.",
        "text": "Hänge diese Karte an Taskmaster an. Hänge sie ansonsten an den gegnerischen Anführer an.\n[star] Die Angriffe des Charakters mit diesem Anhang erhalten Durchdringend.\n<b>Held - Aktion</b>: Gib [mental] [physical]-Ressourcen aus → lege diese Karte ab.",
    },
    {
        "code": "57024",
        "name": "Taskmasters Schild",
        "traits": "Rüstung.",
        "text": "Hänge diese Karte an Taskmaster an. Hänge sie ansonsten an den gegnerischen Anführer an.\n<b>Erzwungene Unterbrechung</b>: Sobald der Charakter mit diesem Anhang eine beliebige Menge an Schaden nehmen würde, senke die Menge an Schaden um 1.\n<b>Held - Aktion</b>: Gib [mental] [physical]-Ressourcen aus → lege diese Karte ab.",
    },
    {
        "code": "57025",
        "name": "Nachgeahmte Bewegung",
        "text": "<b>Sobald aufgedeckt</b>: Falls Taskmaster im Spiel ist, greift er deinen Anführer an. Gib ansonsten dem gegnerischen Anführer eine Zäh-Statuskarte und eine verdeckte Boost-Karte.\n<hr />\n[star] <b>Boost</b>: Gib dem aktivierten Gegner eine zusätzliche Boost-Karte.",
    },
    {
        "code": "57026",
        "name": "Taskmasters Akademie",
        "flavor": "„Du denkst, ich bin zu hart? Warte nur, bis du gegen Steve Rogers kämpfst!\" -Taskmaster",
        "text": "Hindernis 1[per_hero].\n<b>Sobald besiegt</b>: Gib dem gegnerischen Anführer eine Zäh-Statuskarte und eine verdeckte Boost-Karte.",
    },
    # Deadly Duo modular
    {
        "code": "57027",
        "name": "Jester",
        "flavor": "„Ha ha! Das ist einfach zu schön! Sie befehlen uns doch tatsächlich, Helden anzugreifen!\"",
        "traits": "Thunderbolt.",
        "text": "<b>Sobald aufgedeckt</b>: Lege die obersten 3 Karten deines Decks ab. Nimm für jeden unterschiedlichen Kartentyp, der auf diese Weise abgelegt wurde, 1 indirekten Schaden.",
    },
    {
        "code": "57028",
        "name": "Jack O'Lantern",
        "flavor": "„Ich kann nicht glauben, dass wir hierfür bezahlt werden!\"",
        "traits": "Thunderbolt.",
        "text": "<b>Sobald aufgedeckt</b>: Lege die obersten 3 Karten deines Decks ab. Platziere für jeden unterschiedlichen Kartentyp, der auf diese Weise abgelegt wurde, 1 Bedrohung auf dem Hauptplan.",
    },
    {
        "code": "57029",
        "name": "Mad Jacks Plattform",
        "traits": "Tech.",
        "text": "Hänge diese Karte an einen Schergen nach Wahl des gegnerischen Teams an. Ansonsten erhält diese Karte Nachrüsten.\nDer Scherge mit diesem Anhang bekommt +4 Lebenspunkte und erhält Gestählt.\n<hr />\n[star] <b>Boost</b>: Hänge diese Karte an einen Schergen im Kampf mit dir an.",
    },
    {
        "code": "57030",
        "name": "Jesters Jo-Jo",
        "text": "<b>Sobald aufgedeckt</b>: Lege die Karte mit den höchsten Kosten unter deiner Kontrolle ab. Ansonsten erhält diese Karte Nachrüsten.\n<hr />\n[star] <b>Boost</b>: Lege ein Upgrade unter deiner Kontrolle ab.",
    },
    {
        "code": "57031",
        "name": "Tödliches Duo",
        "flavor": "Im Auftrag von S.H.I.E.L.D. jagen Jester und Jack O'Lantern abtrünnige Helden, was sie nur allzu gerne tun.",
        "text": "Hindernis 1[per_hero].\n<b>Sobald besiegt</b>: Jeder Spieler legt die obersten 8 Karten seines Decks ab.",
    },
    # Standard PVP duplicates 36-39
    {
        "code": "57036",
        "name": "Gerechte Sache",
        "flavor": "„Ich war jahrelang Doppelagentin. Für eine gerechte Sache würde ich fast alles tun.\" -Spider-Woman",
        "text": "<b>Sobald aufgedeckt</b>: Der gegnerische Anführer treibt den Plan voran. Falls in deinem Team mehr als 1 Spieler ist, gib dem gegnerischen Anführer für diese Aktivierung eine zusätzliche Boost-Karte.",
    },
    {
        "code": "57037",
        "name": "Was immer nötig ist",
        "flavor": "„Ziel im Visier. Angriff einleiten.\" -Captain Marvel",
        "text": "<b>Sobald aufgedeckt (Alter Ego)</b>: Der gegnerische Anführer greift deinen Anführer an.\n<b>Sobald aufgedeckt (Held)</b>: Der gegnerische Anführer greift dich an.",
    },
    {
        "code": "57038",
        "name": "Gezielter Angriff",
        "text": "<b>Sobald aufgedeckt</b>: Das gegnerische Team durchsucht die obersten 5 Karten des Begegnungsdecks nach einer Karte und teilt sie dir als verdeckte Begegnungskarte zu.\n<hr />\n[star] <b>Boost</b>: Diese Karte erhält [crisis] für jeden Spieler in deinem Team.",
    },
    {
        "code": "57039a",
        "name": "Eine Seite wählen",
        "text": "Dauerhaft.\nDer gegnerische Anführer kann nicht mehr als 2 Schaden durch jeden Angriff nehmen.\n<b>Erzwungene Reaktion</b>: Nachdem die letzte Bedrohung von dieser Karte entfernt worden ist, durchsucht das gegnerische Team die obersten 5 Karten des Begegnungsdecks nach 1[per_hero] Begegnungskarte und teilt jedem Spieler eine davon als verdeckte Begegnungskarte zu. Drehe diese Karte um.",
    },
    {
        "code": "57039b",
        "name": "Jetzt wird's persönlich",
        "text": "<i>Gib diese Karte dem Startspieler.</i>\n<b>Aktion</b>: Entferne diese Karte aus dem Spiel → jeder Spieler in deinem Team wählt 2 der beiseitegelegten Spielerkarten deines Anführers und nimmt sie auf seine Hand.",
    },

    # Vision leader I-IV
    {
        "code": "57040",
        "name": "Vision",
        "traits": "Avenger. Fliegend.",
        "text": "<b>Spielaufbau</b>: Das gegnerische Team findet Visions Massegestalt-Anhang und hängt ihn mit der Festkörper-Seite nach oben an Vision an.\n<b>Erzwungene Reaktion</b>: Nachdem Schritt 1 der Schurkenphase abgehandelt worden ist, drehe Visions Massegestalt-Anhang um.",
    },
    {
        "code": "57041",
        "name": "Vision",
        "traits": "Avenger. Fliegend.",
        "text": "Standhaft.\n<b>Sobald aufgedeckt</b>: Teile jedem Spieler eine Begegnungskarte zu. Vision kann in dieser Phase keinen Schaden nehmen.\n<b>Erzwungene Reaktion</b>: Nachdem Schritt 1 der Schurkenphase abgehandelt worden ist, drehe Visions Massegestalt-Anhang um.",
    },
    {
        "code": "57042",
        "name": "Vision",
        "traits": "Avenger. Fliegend.",
        "text": "<b>Spielaufbau</b>: Das gegnerische Team findet Visions Massegestalt-Anhang und hängt ihn mit der Festkörper-Seite nach oben an Vision an.\n<b>Erzwungene Reaktion</b>: Nachdem Schritt 1 der Schurkenphase abgehandelt worden ist, drehe Visions Massegestalt-Anhang um.",
    },
    {
        "code": "57043",
        "name": "Vision",
        "traits": "Avenger. Fliegend.",
        "text": "Standhaft.\n<b>Sobald aufgedeckt</b>: Teile jedem Spieler eine Begegnungskarte zu. Vision kann in dieser Phase keinen Schaden nehmen.\n<b>Erzwungene Reaktion</b>: Nachdem Schritt 1 der Schurkenphase abgehandelt worden ist, drehe Visions Massegestalt-Anhang um.",
    },
    # Main schemes Resistance
    {
        "code": "57044a",
        "name": "Superhelden im Untergrund",
        "text": "<b>Inhalt</b>: Gewählter Anführer (I) und (II) <i>(stattdessen (III) und (IV) im Expertenmodus)</i>. Set des gewählten Anführers, Standard-Begegnungsset und 3-4 modulare Sets.\n<b>Spielaufbau</b>: Im kompetitiven Modus findet das gegnerische Team den Nebenplan Eine Seite wählen und dein Team deckt ihn auf. Finde im kooperativen Modus den Nebenplan des gewählten Anführers und decke ihn auf.",
    },
    {
        "code": "57044b",
        "name": "Geheime Identitäten schützen",
        "flavor": "Ohne ihre Maskierung bringen die Helden ihre Angehörigen und sich selbst in Gefahr.",
        "text": "Falls in deinem Team mehr als 1 Spieler ist, erhält dieser Abschnitt Hindernis 2[per_hero].\n[star] <b>Erzwungene Reaktion</b>: Nachdem Schritt 1 der Schurkenphase abgehandelt worden ist, legt jeder Spieler die obersten 3 Karten seines Decks ab.",
    },
    {
        "code": "57045a",
        "name": "Untergrund-Taktiken",
        "flavor": "Captain America und seine Avengers verweigern ihre Registrierung bei S.H.I.E.L.D. und sind gezwungen, in den Untergrund zu gehen, um nicht verhaftet zu werden. Als Iron Man und Captain Marvel beginnen, ihre Superhelden-Freunde einzusperren, beschließen die Helden im Untergrund, Widerstand zu leisten.",
    },
    {
        "code": "57045b",
        "name": "Machtmissbrauch enthüllen",
        "flavor": "„Wenn wir das geheime Gefängnis von S.H.I.E.L.D. vor der ganzen Welt enthüllen, werden sie die öffentliche Unterstützung verlieren.\" -Vision",
        "text": "Verbündete kommen erschöpft ins Spiel.\n<b>Falls dieser Abschnitt vollendet ist, verlieren die Spieler das Spiel.</b>",
    },
    # Vision leader attachments
    {
        "code": "57046a",
        "name": "Festkörper",
        "flavor": "Vision kontrolliert die Moleküle seines Körpers, um sich immateriell zu machen oder sie so dicht anzuordnen, dass Waffen an ihm zerschellen.",
        "traits": "Superkraft.",
        "text": "Dauerhaft. Massegestalt.",
    },
    {
        "code": "57046b",
        "name": "Immateriell",
        "flavor": "„Innovation ist die ultimative Waffe.\" -Vision",
        "traits": "Superkraft.",
        "text": "Dauerhaft. Massegestalt.\n<b>Erzwungene Unterbrechung</b>: Sobald Vision eine beliebige Menge an Schaden nehmen würde, senke die Menge an Schaden um 1.",
    },
    {
        "code": "57047",
        "name": "Solarjuwel",
        "traits": "Gegenstand.",
        "text": "Hänge diese Karte an Vision an.\nVision erhält Gestählt.\n<b>Held - Reaktion</b>: Nachdem du einen Basisangriff gegen Vision durchgeführt hast, gib [energy] [physical]-Ressourcen aus → lege diese Karte ab und drehe Visions Massegestalt-Anhang um.\n<hr />\n[star] <b>Boost</b>: Decke diese Karte auf.",
    },
    {
        "code": "57048",
        "name": "Visions Umhang",
        "traits": "Gegenstand.",
        "text": "Hänge diese Karte an Vision an.\nVision erhält Vergeltung 1.\n<b>Held - Reaktion</b>: Nachdem du einen Basisangriff gegen Vision durchgeführt hast, gib [energy] [mental]-Ressourcen aus → lege diese Karte ab und drehe Visions Massegestalt-Anhang um.\n<hr />\n[star] <b>Boost</b>: Decke diese Karte auf.",
    },
    {
        "code": "57049",
        "name": "Massenverdichtung",
        "flavor": "„Stopp!\" -Vision",
        "traits": "Superkraft.",
        "text": "Hänge diese Karte an Vision an.\n<b>Erzwungene Unterbrechung</b>: Sobald ein Charakter Vision angreift, solange der Festkörper-Anhang im Spiel ist, verhindere allen Schaden durch den Angriff und betäube den angreifenden Charakter. Lege diese Karte ab.",
    },
    {
        "code": "57050",
        "name": "Dichtekontrolle",
        "traits": "Superkraft.",
        "text": "Nachrüsten. Hänge diese Karte an Vision an.\n<b>Erzwungene Unterbrechung</b>: Sobald Vision aktiviert wird und falls diese Aktivierung:\n• den Plan vorantreibt, drehe Visions Massegestalt-Anhang auf die Immateriell-Seite um.\n• ein Angriff ist, drehe Visions Massegestalt-Anhang auf die Festkörper-Seite um.\nLege dann diese Karte ab, falls Visions Massegestalt-Anhang umgedreht wurde.",
    },
    {
        "code": "57051",
        "name": "Solarstrahl",
        "text": "<b>Sobald aufgedeckt (Alter Ego)</b>: Vision treibt den Plan voran. Falls der Immateriell-Anhang im Spiel ist, bekommt Vision für diese Aktivierung +1 PLA.\n<b>Sobald aufgedeckt (Held)</b>: Vision greift dich an. Falls der Festkörper-Anhang im Spiel ist, bekommt Vision für diesen Angriff +1 ANG.",
    },
    {
        "code": "57052",
        "name": "Superfester Schlag",
        "flavor": "„Bitte leiste keinen Widerstand, sonst bin ich gezwungen, noch mehr Gewalt anzuwenden.\" -Vision",
        "text": "<b>Sobald aufgedeckt</b>: Erschöpfe einen Charakter unter deiner Kontrolle. Falls der Festkörper-Anhang im Spiel ist, füge dem Charakter 2 Schaden zu. Falls der Immateriell-Anhang im Spiel ist, drehe den Anhang um.",
    },
    {
        "code": "57053",
        "name": "Phasenunterbrechung",
        "flavor": "„Ziel neutralisiert.\" -Vision",
        "text": "<b>Sobald aufgedeckt</b>: Das gegnerische Team erschöpft ein Upgrade unter deiner Kontrolle. Falls der Immateriell-Anhang im Spiel ist, lege das Upgrade stattdessen ab. Falls der Festkörper-Anhang im Spiel ist, drehe ihn um.",
    },
    {
        "code": "57054",
        "name": "Auf der Durchreise",
        "flavor": "Visions Kraft der Phasenkontrolle macht ihn zu einem schwierigen und unberechenbaren Gegner.",
        "text": "<b>Sobald besiegt</b>: Der Spieler, der diesen Plan besiegt hat, verwirrt seine Identität. Ansonsten betäubt er seine Identität.",
    },
]

result = add_cards(cards)
print('added:', len(result['added']))
print('skipped:', len(result['skipped']))
print('total:', result['total'])
