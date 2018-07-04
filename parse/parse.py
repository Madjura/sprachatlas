from pyparsing import *

# vokale
grundwert_vokal = (CaselessLiteral("A") | CaselessLiteral("E") | CaselessLiteral("I") | CaselessLiteral("O") |
                   CaselessLiteral("U") | CaselessLiteral("O=") | CaselessLiteral("U="))("Grundwert")
halbvokal = (CaselessLiteral("U;") | CaselessLiteral("I;") | CaselessLiteral("E;"))("Halbvokal")
grundwerte_vokal_basis = grundwert_vokal | halbvokal  # combinable but not the reduktionsvokale!
reduktionsvokal = (CaselessLiteral("E,") | CaselessLiteral("A,"))("Reduktionsvokal")
grundzeichen_vokal = (grundwert_vokal | halbvokal | reduktionsvokal)("Grundzeichen")

# variationen
offnungsgrad = Combine(grundwerte_vokal_basis + Optional(Literal("1") | Literal("2") | Literal("5") | Literal("6")))\
    ("Öffnungsgrad")
offnungsgrad_halbwert = Combine(grundwert_vokal + (Literal("1.") | Literal("2.") | Literal("5.") | Literal("6.")))\
    ("Öffnungsgrad (Halbwert)")

# can be grundwerte_vokal_basis + the literals OR offnungsgrad + the literals
rundung = Combine((offnungsgrad | grundwerte_vokal_basis) + (Literal("=.") | Literal("=") | Literal("==.") | Literal("==")))("Rundung")
# can be grundwerte_vokal_basis + the literals OR rundung + the literals
palatovelare = Combine((rundung | grundwerte_vokal_basis) + (Literal("$") | Literal("$.") | Literal("$$")))("Palatovelare")
# can be grundwerte_vokal_basis + the literals OR palatovelare + the literals
nasalierung = Combine((palatovelare | grundwerte_vokal_basis) + Literal("+") + Optional(Literal("..") | Literal(".")
                                                                                        | Literal("1")))("Nasalierung")
quantitat = Combine((nasalierung | grundwerte_vokal_basis) + Literal("-") + Optional(Literal("1") | Literal("2")
                                                                                     | Literal("3")))("Quantität")
reduktion = Combine((quantitat | grundwerte_vokal_basis) + OneOrMore(Literal("&")))("Reduktion")
grenzwert = Combine((reduktion | grundwerte_vokal_basis) + grundwerte_vokal_basis + Literal(":"))("Grenzwert")
akzent = Combine((grenzwert | grundwerte_vokal_basis) + Literal("'") + Optional(Literal("1")))("Akzent")
silbentrager = Combine((akzent | grundwerte_vokal_basis) + (Literal("4") | Literal("4.")))("Silbenträger")

vokale = (silbentrager | akzent | grenzwert | reduktion | nasalierung | palatovelare | rundung
          | offnungsgrad_halbwert | offnungsgrad | reduktionsvokal | halbvokal | grundwert_vokal)("Vokale")

##########
# konsonanten
# grundzeichen
konsonanten_basis = (CaselessLiteral("B") | CaselessLiteral("C") | CaselessLiteral("D") | CaselessLiteral("F")
                     | CaselessLiteral("G") | CaselessLiteral("H") | CaselessLiteral("K") | CaselessLiteral("L") \
                     | CaselessLiteral("M") | CaselessLiteral("N") | CaselessLiteral("P") | CaselessLiteral("Q") \
                     | CaselessLiteral("R") | CaselessLiteral("S") | CaselessLiteral("T") | CaselessLiteral("V") \
                     | CaselessLiteral("W") | CaselessLiteral("X") | CaselessLiteral("Y") | CaselessLiteral("Z"))\
    ("Konsonant")
grenzwert_konsonant = Combine(konsonanten_basis + konsonanten_basis + Literal(":"))("Grenzwert (Konsonant)")
fortisierung = Combine((grenzwert_konsonant | konsonanten_basis) + (Literal("2") | Literal("22")))("Fortisierung")
lenisierung = Combine((fortisierung | konsonanten_basis) + (Literal("1") | Literal("11")))("Lenisierung")
stimmhaftigkeit = Combine((lenisierung | konsonanten_basis) + Literal("%"))("Stimmhaftigkeit")
implosion = Combine((stimmhaftigkeit | konsonanten_basis) + Literal("%"))("Implosion")
quantitat_konsonant = Combine((implosion | konsonanten_basis) + Literal("-"))("Quantität (Konsonant)")
reduktion_konsonant = Combine((quantitat_konsonant | konsonanten_basis) + Literal("&"))("Reduktion (Konsonant)")
kehlkopfverschluss = Combine(CaselessLiteral("H") + Literal(","))("Kehlkopfverschluss")
silbische_funktion = (CaselessLiteral("M4") | CaselessLiteral("M4.") | CaselessLiteral("N4") | CaselessLiteral("N4.")
                      | CaselessLiteral("R4") | CaselessLiteral("R4."))("Silbische Funktion")
spirantisierung = (CaselessLiteral("B7") | CaselessLiteral("D7") | CaselessLiteral("G7"))("Spirantisierung")
bilabiale_reibelaute = (CaselessLiteral("V6") | CaselessLiteral("W"))("Bilabiale Reibelaute")


s_laute = Combine(CaselessLiteral("S") + (Literal("7") | Literal("8") | Literal("86") | Literal("9") | Literal("6") |
                                          Literal("6.")))("s-Laut")
ich_laute = (CaselessLiteral("X7") | CaselessLiteral("X7.") | CaselessLiteral("78"))("Ich-Laut")
ach_laute = (CaselessLiteral("X6") | CaselessLiteral("X6.") | CaselessLiteral("X68") | CaselessLiteral("X")
             | CaselessLiteral("X8"))("Ach-Laut")
nasale = (CaselessLiteral("N7") | CaselessLiteral("N7.") | CaselessLiteral("M7"))("Nasale")
r_laute = (CaselessLiteral("R") + Optional(Literal(",") | Literal("9") | Literal("9.") | Literal("7") | Literal("7,")
                                           | Literal("8") | Literal("6") | Literal("8%")))("r-Laut")
r_reduktion = Combine(CaselessLiteral("r") + (Literal("&") | Literal(",&") | Literal("7&") | Literal("&&")))\
    ("R-Reduktion")
l_laute = Combine(CaselessLiteral("L") + Optional(Literal("$") | Literal("7") | Literal("7.") | Literal("77")
                                                  | Literal("9") | Literal("9.") | Literal(";")))("L-Laute")
konsonanten = l_laute | r_reduktion | r_laute | nasale | ach_laute | ich_laute | s_laute | bilabiale_reibelaute \
              | spirantisierung | silbische_funktion | kehlkopfverschluss | reduktion_konsonant | quantitat_konsonant \
              | implosion | stimmhaftigkeit | lenisierung | fortisierung | grenzwert_konsonant | konsonanten_basis

konsonant_or_vokal = konsonanten | vokale

parse_all = OneOrMore(konsonant_or_vokal)

#u5-2nd2a2vi5-s7we2ne,u5-2ndn4gs7da5-2ndni-s
for match in quantitat.scanString("u5-2"):
    print(match)

raise Exception
for match in vokale.scanString("a2=."):
    r = match[0]
    print(r)


for match in grundwert_vokal.scanString("AEI"):
    r = match[0]
    print(r["Grundwert"])
print("---")
for match in offnungsgrad.scanString("A1"):
    r = match[0]
    print(r["Öffnungsgrad"])
    print(match)
print("---")
for match in offnungsgrad_halbwert.scanString("A1.E5."):
    r = match[0]
    print(r["Öffnungsgrad (Halbwert)"])
print("---")
print("Nasalierung")
for match in nasalierung.scanString("A+..E+.O+I+1"):
    r = match[0]
    print(r)