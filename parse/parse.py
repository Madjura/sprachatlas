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

all_vokal = silbentrager | akzent | grenzwert | reduktion | nasalierung | palatovelare | rundung | offnungsgrad_halbwert | offnungsgrad

##########
# konsonanten
# grundzeichen
konsonanten_basis = CaselessLiteral("B") | CaselessLiteral("C") | CaselessLiteral("D") | CaselessLiteral("F") \
                    | CaselessLiteral("G") | CaselessLiteral("H") | CaselessLiteral("K") | CaselessLiteral("L") \
                    | CaselessLiteral("M") | CaselessLiteral("N") | CaselessLiteral("P") | CaselessLiteral("Q") \
                    | CaselessLiteral("R") | CaselessLiteral("S") | CaselessLiteral("T") | CaselessLiteral("V") \
                    | CaselessLiteral("W") | CaselessLiteral("X") | CaselessLiteral("Y") | CaselessLiteral("Z")
bilabiale_reibelaute = (CaselessLiteral("V6") | CaselessLiteral("F6"))("Bilabiale Reibelaute")
s_laute = (CaselessLiteral("S") + (Literal("6") | Literal("7") | Literal("8") | Literal("9") | Literal("86")))("s-Laut")
# ch_laute = CaselessLiteral("X" + (Literal("7") | Literal("7.") | Literal("78") | Literal("7$") | Literal("7$1")
#                                   | Literal("78$") | Literal("6") | Literal("6.") | Literal("68") | Literal("8")
#                                   | Literal("$") | Literal("8$")))("ch-Laut")
nasale = (CaselessLiteral("N7") | CaselessLiteral("N7.") | CaselessLiteral("M7"))("Nasale")
r_laute = (CaselessLiteral("R") + Optional(Literal(",") | Literal("9") | Literal("9.") | Literal("7") | Literal("7,")
                                           | Literal("8") | Literal("6") | Literal("8%")))("r-Laut")
l_laute = (CaselessLiteral("L") + Optional(Literal("4") | Literal("4.") | Literal("5") | Literal("7") | Literal("77")
                                           | Literal("7.") | Literal("57") | Literal("8") | Literal("9") | Literal(";9")
                                           | Literal("99") | Literal("$") | Literal("$$") | Literal(";$$") |
                                           Combine(Literal(";") + halbvokal + Literal(":=")) | Literal(";")
                                           | Literal(";$") | CaselessLiteral("D:") | CaselessLiteral("R:")
                                           | CaselessLiteral("D:4") | CaselessLiteral("D&:")
                                           | CaselessLiteral("D&:4")))("l-Laut")
# variationen


for match in all_vokal.scanString("a2=."):
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