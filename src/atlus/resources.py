"""Hold info for the processing script."""

import regex

direction_expand = {
    "NE": "Northeast",
    "SE": "Southeast",
    "NW": "Northwest",
    "SW": "Southwest",
    "N": "North",
    "E": "East",
    "S": "South",
    "W": "West",
}
"""Compass direction abbreviations."""

name_expand = {
    "ARPT": "airport",
    "BLDG": "building",
    "CONF": "conference",
    "CONV": "convention",
    "CNTR": "center",
    "CTR": "center",
    "DWTN": "downtown",
    "INTL": "international",
    "FT": "fort",
    "MT": "mount",
    "MTN": "mountain",
    "SHPG": "shopping",
}
"""Common name abbreviations."""

state_expand = {
    "ALABAMA": "AL",
    "ALA": "AL",
    "ALASKA": "AK",
    "ALAS": "AK",
    "ARIZONA": "AZ",
    "ARIZ": "AZ",
    "ARKANSAS": "AR",
    "ARK": "AR",
    "CALIFORNIA": "CA",
    "CALIF": "CA",
    "CAL": "CA",
    "COLORADO": "CO",
    "COLO": "CO",
    "COL": "CO",
    "CONNECTICUT": "CT",
    "CONN": "CT",
    "DELAWARE": "DE",
    "DEL": "DE",
    "DISTRICT OF COLUMBIA": "DC",
    "FLORIDA": "FL",
    "FLA": "FL",
    "FLOR": "FL",
    "GEORGIA": "GA",
    "GA": "GA",
    "HAWAII": "HI",
    "IDAHO": "ID",
    "IDA": "ID",
    "ILLINOIS": "IL",
    "ILL": "IL",
    "INDIANA": "IN",
    "IND": "IN",
    "IOWA": "IA",
    "KANSAS": "KS",
    "KANS": "KS",
    "KAN": "KS",
    "KENTUCKY": "KY",
    "KEN": "KY",
    "KENT": "KY",
    "LOUISIANA": "LA",
    "MAINE": "ME",
    "MARYLAND": "MD",
    "MASSACHUSETTS": "MA",
    "MASS": "MA",
    "MICHIGAN": "MI",
    "MICH": "MI",
    "MINNESOTA": "MN",
    "MINN": "MN",
    "MISSISSIPPI": "MS",
    "MISS": "MS",
    "MISSOURI": "MO",
    "MONTANA": "MT",
    "MONT": "MT",
    "NEBRASKA": "NE",
    "NEBR": "NE",
    "NEB": "NE",
    "NEVADA": "NV",
    "NEV": "NV",
    "NEW HAMPSHIRE": "NH",
    "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM",
    "N MEX": "NM",
    "NEW M": "NM",
    "NEW YORK": "NY",
    "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND",
    "N DAK": "ND",
    "OHIO": "OH",
    "OKLAHOMA": "OK",
    "OKLA": "OK",
    "OREGON": "OR",
    "OREG": "OR",
    "ORE": "OR",
    "PENNSYLVANIA": "PA",
    "PENN": "PA",
    "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD",
    "S DAK": "SD",
    "TENNESSEE": "TN",
    "TENN": "TN",
    "TEXAS": "TX",
    "TEX": "TX",
    "UTAH": "UT",
    "VERMONT": "VT",
    "VIRGINIA": "VA",
    "WASHINGTON": "WA",
    "WASH": "WA",
    "WEST VIRGINIA": "WV",
    "W VA": "WV",
    "WISCONSIN": "WI",
    "WIS": "WI",
    "WISC": "WI",
    "WYOMING": "WY",
    "WYO": "WY",
    "ONTARIO": "ON",
    "QUEBEC": "QC",
    "NOVA SCOTIA": "NS",
    "NEW BRUNSWICK": "NB",
    "MANITOBA": "MB",
    "BRITISH COLUMBIA": "BC",
    "PRINCE EDWARD ISLAND": "PE",
    "PRINCE EDWARD": "PE",
    "SASKATCHEWAN": "SK",
    "ALBERTA": "AB",
    "NEWFOUNDLAND AND LABRADOR": "NL",
    "NEWFOUNDLAND & LABRADOR": "NL",
    "NEWFOUNDLAND": "NL",
    "YUKON": "YK",
    "NUNAVUT": "NU",
    "NORTHWEST TERRITORIES": "NT",
    "NW TERRITORIES": "NT",
}
"""Map states to abbreviations."""

street_expand = {
    "ACC": "ACCESS",
    "ALY": "ALLEY",
    "ANX": "ANEX",
    "ARC": "ARCADE",
    "AV": "AVENUE",
    "AVE": "AVENUE",
    "BYU": "BAYOU",
    "BCH": "BEACH",
    "BND": "BEND",
    "BLF": "BLUFF",
    "BLFS": "BLUFFS",
    "BTM": "BOTTOM",
    "BLVD": "BOULEVARD",
    "BR": "BRANCH",
    "BRG": "BRIDGE",
    "BRK": "BROOK",
    "BRKS": "BROOKS",
    "BG": "BURG",
    "BGS": "BURGS",
    "BYP": "BYPASS",
    "CP": "CAMP",
    "CY": "KEY",
    "CYN": "CANYON",
    "CPE": "CAPE",
    "CTR": "CENTER",
    "CTRS": "CENTERS",
    "CIR": "CIRCLE",
    "CIRS": "CIRCLES",
    "CLF": "CLIFF",
    "CLFS": "CLIFFS",
    "CLB": "CLUB",
    "CMN": "COMMON",
    "CMNS": "COMMONS",
    "COR": "CORNER",
    "CORS": "CORNERS",
    "CRSE": "COURSE",
    "CT": "COURT",
    "CTS": "COURTS",
    "CV": "COVE",
    "CVS": "COVES",
    "CRK": "CREEK",
    "CRES": "CRESCENT",
    "CRST": "CREST",
    "CSWY": "CAUSEWAY",
    "CURV": "CURVE",
    "DL": "DALE",
    "DM": "DAM",
    "DV": "DIVIDE",
    "DR": "DRIVE",
    "DRS": "DRIVES",
    "EST": "ESTATE",
    "EXPY": "EXPRESSWAY",
    "EXPWY": "EXPRESSWAY",
    "EXT": "EXTENSION",
    "EXTS": "EXTENSIONS",
    "FGR": "FORGE",
    "FGRS": "FORGES",
    "FLS": "FALLS",
    "FLD": "FIELD",
    "FLDS": "FIELDS",
    "FLT": "FLAT",
    "FLTS": "FLATS",
    "FRD": "FORD",
    "FRDS": "FORDS",
    "FRST": "FOREST",
    "FRG": "FORGE",
    "FRGS": "FORGES",
    "FRK": "FORK",
    "FRKS": "FORKS",
    "FRY": "FERRY",
    "FRYS": "FERRYS",
    "FOR": "FORD",
    "FORS": "FORDS",
    "FT": "FORT",
    "FWY": "FREEWAY",
    "GD": "GRADE",
    "GDN": "GARDEN",
    "GDNS": "GARDENS",
    "GTWY": "GATEWAY",
    "GLN": "GLEN",
    "GLNS": "GLENS",
    "GN": "GREEN",
    "GNS": "GREENS",
    "GRN": "GREEN",
    "GRNS": "GREENS",
    "GRV": "GROVE",
    "GRVS": "GROVES",
    "HBR": "HARBOR",
    "HBRS": "HARBORS",
    "HGWY": "HIGHWAY",
    "HVN": "HAVEN",
    "HTS": "HEIGHTS",
    "HWY": "HIGHWAY",
    "HL": "HILL",
    "HLS": "HILLS",
    "HOLW": "HOLLOW",
    "INLT": "INLET",
    "IS": "ISLAND",
    "ISS": "ISLANDS",
    "JCT": "JUNCTION",
    "JCTS": "JUNCTIONS",
    "KY": "KEY",
    "KYS": "KEYS",
    "KNL": "KNOLL",
    "KNLS": "KNOLLS",
    "LK": "LAKE",
    "LKS": "LAKES",
    "LNDG": "LANDING",
    "LN": "LANE",
    "LGT": "LIGHT",
    "LGTS": "LIGHTS",
    "LF": "LOAF",
    "LCK": "LOCK",
    "LCKS": "LOCKS",
    "LDG": "LODGE",
    "LP": "LOOP",
    "MNR": "MANOR",
    "MNRS": "MANORS",
    "MDW": "MEADOW",
    "MDWS": "MEADOWS",
    "ML": "MILL",
    "MLS": "MILLS",
    "MSN": "MISSION",
    "MTWY": "MOTORWAY",
    "MT": "MOUNT",
    "MTN": "MOUNTAIN",
    "MTNS": "MOUNTAINS",
    "NCK": "NECK",
    "ORCH": "ORCHARD",
    "OPAS": "OVERPASS",
    "PKY": "PARKWAY",
    "PKWY": "PARKWAY",
    "PSGE": "PASSAGE",
    "PNE": "PINE",
    "PNES": "PINES",
    "PL": "PLACE",
    "PLN": "PLAIN",
    "PLNS": "PLAINS",
    "PLZ": "PLAZA",
    "PT": "POINT",
    "PTS": "POINTS",
    "PRT": "PORT",
    "PRTS": "PORTS",
    "PR": "PRAIRIE",
    "PVT": "PRIVATE",
    "RADL": "RADIAL",
    "RNCH": "RANCH",
    "RPD": "RAPID",
    "RPDS": "RAPIDS",
    "RST": "REST",
    "RDG": "RIDGE",
    "RDGS": "RIDGES",
    "RIV": "RIVER",
    "RD": "ROAD",
    "RDS": "ROADS",
    "RT": "ROUTE",
    "RTE": "ROUTE",
    "SHL": "SHOAL",
    "SHLS": "SHOALS",
    "SHR": "SHORE",
    "SHRS": "SHORES",
    "SKWY": "SKYWAY",
    "SPG": "SPRING",
    "SPGS": "SPRINGS",
    "SQ": "SQUARE",
    "SQS": "SQUARES",
    "STA": "STATION",
    "STRA": "STRAVENUE",
    "STRM": "STREAM",
    "STS": "STREETS",
    "SMT": "SUMMIT",
    "SRVC": "SERVICE",
    "TER": "TERRACE",
    "TRWY": "THROUGHWAY",
    "THFR": "THOROUGHFARE",
    "TRCE": "TRACE",
    "TRAK": "TRACK",
    "TRFY": "TRAFFICWAY",
    "TRL": "TRAIL",
    "TRLR": "TRAILER",
    "TUNL": "TUNNEL",
    "TPKE": "TURNPIKE",
    "UPAS": "UNDERPASS",
    "UN": "UNION",
    "UNP": "UNDERPASS",
    "UNS": "UNIONS",
    "VIA": "VIADUCT",
    "VIAS": "VIADUCTS",
    "VLY": "VALLEY",
    "VLYS": "VALLEYS",
    "VW": "VIEW",
    "VWS": "VIEWS",
    "VLG": "VILLAGE",
    "VL": "VILLE",
    "VIS": "VISTA",
    "WK": "WALK",
    "WKWY": "WALKWAY",
    "WY": "WAY",
    "WL": "WELL",
    "WLS": "WELLS",
    "XING": "CROSSING",
    "XINGS": "CROSSINGS",
    "XRD": "CROSSROAD",
    "XRDS": "CROSSROADS",
    "YU": "BAYOU",
}
"""Common street type abbreviations."""

saints = [
    "Abigail",
    "Agatha",
    "Agnes",
    "Andrew",
    "Anthony",
    "Augustine",
    "Bernadette",
    "Brigid",
    "Catherine",
    "Charles",
    "Christopher",
    "Clare",
    "Cloud",
    "Dymphna",
    "Elizabeth",
    "Faustina",
    "Felix",
    "Francis",
    "Gabriel,",
    "George",
    "Gerard",
    "James",
    "Joan",
    "John",
    "Joseph",
    "Jude",
    "Kateri",
    "Louis",
    "Lucie",
    "Lucy",
    "Luke",
    "Maria",
    "Mark",
    "Martin",
    "Mary",
    "Maximilian",
    "Michael",
    "Monica",
    "Padre",
    "Patrick",
    "Paul",
    "Peter",
    "Philomena",
    "Raphael",
    "Rita",
    "Rose",
    "Sebastian",
    "Teresa",
    "Therese",
    "Thomas",
    "Valentine",
    "Victor",
    "Vincent",
]
"""Most common saint names."""

bad_zip_first_3 = [
    "001",
    "002",
    "003",
    "004",
    "213",
    "269",
    "343",
    "345",
    "348",
    "353",
    "419",
    "428",
    "429",
    "517",
    "518",
    "519",
    "529",
    "533",
    "536",
    "552",
    "568",
    "569",
    "578",
    "579",
    "589",
    "621",
    "632",
    "642",
    "643",
    "659",
    "663",
    "682",
    "694",
    "695",
    "696",
    "697",
    "698",
    "699",
    "702",
    "709",
    "715",
    "732",
    "742",
    "817",
    "818",
    "819",
    "839",
    "848",
    "849",
    "851",
    "854",
    "858",
    "861",
    "862",
    "866",
    "867",
    "868",
    "869",
    "876",
    "886",
    "887",
    "888",
    "892",
    "896",
    "899",
    "909",
    "929",
    "987",
]
"""Three-digit combinations that don't represent a zip code."""

# pre-compile regex for speed
ABBR_JOIN = "|".join({**name_expand, **street_expand})
abbr_join_comp = regex.compile(
    rf"(\b(?:{ABBR_JOIN})\b\.?)(?!')", flags=regex.IGNORECASE
)

DIR_FILL = "|".join(r"\.?".join(list(abbr)) for abbr in direction_expand)
st_ave = r" (?:Street|Avenue)"
dir_fill_comp = regex.compile(
    rf"(?<!(?:^(?:Avenue) |[\.']))(\b(?:{DIR_FILL})\b\.?)(?!(?:\.?[a-zA-Z]|{st_ave}))",
    flags=regex.IGNORECASE,
)

sr_comp = regex.compile(r"(\bS\.?R\b\.?)(?= \d+)", flags=regex.IGNORECASE)

saint_comp = regex.compile(
    rf"^(St\.?)(?= )|(\bSt\.?)(?= (?:{'|'.join(saints)}))", flags=regex.IGNORECASE
)

street_comp = regex.compile(
    r"St\.?(?= [NESW]\.?[EW]?\.?)|(?<=\d[thndstr]{2} )St\.?\b|St\.?$"
)

post_comp = regex.compile(r"(\d{5})-?0{4}")

usa_comp = regex.compile(r",? (?:USA?|United States(?: of America)?|Canada)\b")

paren_comp = regex.compile(r" ?\(.*\)")

# match Wisconsin grid-style addresses: N65w25055, W249 N6620, etc.
grid_comp = regex.compile(
    r"\b([NnSs]\d{2,}\s*[EeWw]\d{2,}|[EeWw]\d{2,}\s*[NnSs]\d{2,})\b"
)

phone_comp = regex.compile(
    r"^\(?(?:\+? ?1?[ -.]*)?(?:\(?(\d{3})\)?[ -.]*)(\d{3})[ -.]*(\d{4})$"
)

day_expand = {
    "MONDAY": "Mo",
    "MON": "Mo",
    "MO": "Mo",
    "M": "Mo",
    "MONDAYS": "Mo",
    "TUESDAY": "Tu",
    "TUES": "Tu",
    "TUE": "Tu",
    "TU": "Tu",
    "TUESDAYS": "Tu",
    "WEDNESDAY": "We",
    "WEDS": "We",
    "WED": "We",
    "WE": "We",
    "W": "We",
    "WEDNESDAYS": "We",
    "THURSDAY": "Th",
    "THURS": "Th",
    "THUR": "Th",
    "THU": "Th",
    "THR": "Th",
    "TH": "Th",
    "THURSDAYS": "Th",
    "FRIDAY": "Fr",
    "FRI": "Fr",
    "FR": "Fr",
    "FI": "Fr",  # surpisingly common in OSM, maybe typo in some software
    "F": "Fr",
    "FRIDAYS": "Fr",
    "SATURDAY": "Sa",
    "SAT": "Sa",
    "SA": "Sa",
    "SATS": "Sa",
    "SATURDAYS": "Sa",
    "SUNDAY": "Su",
    "SUN": "Su",
    "SU": "Su",
    "SUNDAYS": "Su",
    "SUNS": "Su",
    # Spanish
    "LUNES": "Mo",
    "LUN": "Mo",
    "MARTES": "Tu",
    "MAR": "Tu",
    "MIERCOLES": "We",
    "MIÉRCOLES": "We",
    "MIE": "We",
    "JUEVES": "Th",
    "JUE": "Th",
    "VIERNES": "Fr",
    "VIE": "Fr",
    "SABADO": "Sa",
    "SÁBADO": "Sa",
    "SABADOS": "Sa",
    "SÁBADOS": "Sa",
    "SAB": "Sa",
    "DOMINGO": "Su",
    "DOMINGOS": "Su",
    # French
    "LUNDI": "Mo",
    "MARDI": "Tu",
    "MERCREDI": "We",
    "JEUDI": "Th",
    "VENDREDI": "Fr",
    "SAMEDI": "Sa",
    "DIMANCHE": "Su",
    # German
    "MONTAG": "Mo",
    "DIENSTAG": "Tu",
    "MITTWOCH": "We",
    "DONNERSTAG": "Th",
    "FREITAG": "Fr",
    "SAMSTAG": "Sa",
    "SONNTAG": "Su",
    # public holiday indicator -- a real "8th day" in OSM syntax, with no
    # other accepted aliases or forms
    "PH": "PH",
}
"""Map day names/abbreviations to OSM two-letter day codes."""

day_order = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
"""Canonical OSM day ordering."""

day_index = {day: i for i, day in enumerate(day_order)}
"""Map day codes to their position in the week, for fast O(1) lookups."""

DAY_ALT = "|".join(sorted(day_expand, key=len, reverse=True))
# Avoid matching single-letter days (M, W, F) when preceded by a period
# (e.g., "a.m.", "p.m.") -- use negative lookbehind
day_comp = regex.compile(
    rf"(?<![a-zA-Z]\.)\b(?:{DAY_ALT})\b\.?", flags=regex.IGNORECASE
)

# looser day-name detector that also matches when a day name is glued
# directly to a following digit with no separator (e.g. "Friday10:00 AM"),
# used only to detect the *presence* of day info rather than to extract it
day_present_comp = regex.compile(
    rf"\b(?:{DAY_ALT})(?![a-zA-Z])", flags=regex.IGNORECASE
)

day_range_comp = regex.compile(
    rf"\b(?:{DAY_ALT})\b\.?(?:\s*(?:-|to|through|thru|a|\u2013|\u2014|\u2015)\s*\b(?:{DAY_ALT})\b\.?)?",
    flags=regex.IGNORECASE,
)

weekday_comp = regex.compile(r"\bweekdays?\b", flags=regex.IGNORECASE)
weekend_comp = regex.compile(r"\bweekends?\b", flags=regex.IGNORECASE)
daily_comp = regex.compile(
    r"\b(?:daily|every ?day|todos los dias)\b", flags=regex.IGNORECASE
)
closed_comp = regex.compile(r"\b(?:closed|off)\b", flags=regex.IGNORECASE)
day_24_comp = regex.compile(
    r"\b(?:24\s*/\s*7|24\s*hours?(?:\s+a\s+day)?|all\s*day|open\s*24)\b",
    flags=regex.IGNORECASE,
)

# month names, in either abbreviated or full form -- used only to *detect*
# (and reject) calendar/date-based rules that this package doesn't attempt
# to parse, such as "Jan 1 off" or "Dec 25 off"
MONTH_ALT = (
    r"Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?"
    r"|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?"
)
month_comp = regex.compile(rf"\b(?:{MONTH_ALT})\b", flags=regex.IGNORECASE)

# OSM's "nth weekday of month" notation, e.g. "Th[4]" (fourth Thursday) or
# "Su[-1]" (last Sunday) -- also unsupported and rejected outright
nth_weekday_comp = regex.compile(
    rf"\b(?:{DAY_ALT})\s*\[\s*-?\d+\s*\]", flags=regex.IGNORECASE
)

# common named holidays that OSM opening_hours values sometimes reference
# directly instead of (or in addition to) a calendar date -- also
# unsupported and rejected outright
HOLIDAY_ALT = "|".join(
    [
        "easter",
        "good friday",
        "thanksgiving",
        "christmas(?: day|eve)?",
        "boxing day",
        "halloween",
        "new\\s*year'?s?(?:\\s*day)?",
        "victoria day",
        "labou?r day",
        "memorial day",
        "independence day",
        "veterans day",
        "presidents'?\\s*day",
        "columbus day",
        "indigenous peoples'?\\s*day",
        "mlk day",
        "martin luther king,?\\s*jr\\.?\\s*day",
        "juneteenth",
    ]
)
holiday_name_comp = regex.compile(rf"\b(?:{HOLIDAY_ALT})\b", flags=regex.IGNORECASE)

# split a string into multiple top-level rule segments on ";", newlines, a
# middle dot ("·") or bullet ("•"), a slash surrounded by whitespace, or a
# pipe, which are sometimes used as rule separators -- the whitespace
# requirement on the slash keeps it from splitting compact forms like "24/7"
rule_split_comp = regex.compile(
    r"\s*;\s*|\r?\n+\s*|\s*[\u00b7\u2022\u2016\u00A6]\s*|\s+/\s+|\s*\|\s*",
    flags=regex.IGNORECASE,
)

# phrases that carry no day/time information of their own and should be
# discarded entirely wherever they appear (e.g. "Last Seating" following a
# closing time)
ignored_phrase_comp = regex.compile(
    r"\b(last seatings?|last call)\b", flags=regex.IGNORECASE
)

# a comma that introduces a brand new day token, used to further split a
# top-level segment -- only applied when the text before it already looks
# like it contains time/status information (see _split_comma_days)
comma_day_comp = regex.compile(rf",\s*(?=(?:{DAY_ALT})\b)", flags=regex.IGNORECASE)

# whitespace (with no comma/semicolon/etc.) that introduces a brand new day
# token, used to split adjacent rules that have no separator between them
# at all (e.g. "Mo-Fr 08:00-21:00 Sa-Su 08:00-18:00") -- only applied when
# the text before it already looks like a complete day+time rule (see
# _split_space_days), and not when the day word is part of a day range or
# "... to ..." phrase that's already being parsed (e.g. "Monday - Friday")
space_day_comp = regex.compile(
    rf"(?<![-\u2013\u2014,])(?<!\bto)(?<!\bthr(ough|u))(?<!\ba)\s+(?=(?:{DAY_ALT})\b\.?)",
    flags=regex.IGNORECASE,
)

# first place a digit, clock keyword, solar keyword (dawn/dusk/sunrise/
# sunset), or the words "closed"/"off"/"24" appear -- everything before
# this point is assumed to be the "day" portion of a rule segment
time_start_comp = regex.compile(
    r"\d|closed|off|noon|midnight|24\s*/\s*7|24\s*hours?|all\s*day"
    r"|dawn|dusk|sunrise|sunset",
    flags=regex.IGNORECASE,
)

# OSM's solar-relative time keywords, used in place of a clock time (e.g.
# "sunrise-sunset"); rendered in the output exactly as-is, in lowercase
solar_time_comp = regex.compile(
    r"^(?:dawn|dusk|sunrise|sunset)$", flags=regex.IGNORECASE
)

# filler words that may appear in the "day" portion of a segment but carry
# no day information of their own (e.g. "Open 24 hours", or the "at" in
# "Sundays at 7:45 am")
filler_comp = regex.compile(
    r"\b(?:open|hours?|hrs?|at|available)\b", flags=regex.IGNORECASE
)

time_token_comp = regex.compile(
    r"^(\d{1,2})([:.h]?(\d{2}))?\s*([ap]\.?m?\.?)?$", flags=regex.IGNORECASE
)

time_range_split_comp = regex.compile(
    r"\s*(?:-{1,2}|to|through|thru|\ba\b(?!\.?m\.?\b)|\u2013|\u2014|\u2015)\s*",
    flags=regex.IGNORECASE,
)
