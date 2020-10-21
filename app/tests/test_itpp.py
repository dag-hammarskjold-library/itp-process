import os
os.environ['FLASK_TEST'] = 'True'

from unittest import TestCase
from dlx.marc import Bib

class Data(object):
    jbib = {
        '_id' : 999,
        '000' : ['leader'],
        '008' : ['controlfield'],
        '245' : [
            {
                'indicators' : [' ',' '],
                'subfields' : [
                    {
                        'code' : 'a',
                        'value' : 'This'
                    },
                    {
                        'code' : 'b',
                        'value' : 'is the'
                    },
                    {
                        'code' : 'c',
                        'value' : 'title'
                    }
                ]
            }
        ],
        '520' : [
            {
                'indicators' : [' ' ,' '],
                'subfields' : [
                    {
                        'code' : 'a',
                        'value' : 'description'
                    }
                ]
            },
            {
                'indicators' : [' ' ,' '],
                'subfields' : [
                    {
                        'code' : 'a',
                        'value' : 'another description'
                    },
                    {
                        'code' : 'a',
                        'value' : 'repeated subfield'
                    }
                ]
            }
        ],
        '650' : [
            {
                'indicators' : [' ', ' '],
                'subfields' : [
                    {
                        'code' : 'a',
                        'xref' : 777
                    }
                ],
            }
        ],
        '710' : [
            {
                'indicators' : [' ',' '],
                'subfields' : [
                    {
                        'code' : 'a',
                        'xref' : 333
                    }
                ]
            }
        ]
    }
    
    jbib2 = {
        '_id' : 555,
        '000' : ['leader'],
        '245' : [
            {
                'indicators' : [' ',' '],
                'subfields' : [
                    {
                        'code' : 'a',
                        'value' : 'Another'
                    },
                    {
                        'code' : 'b',
                        'value' : 'is the'
                    },
                    {
                        'code' : 'c',
                        'value' : 'title'
                    }
                ]
            }
        ],
        '650' : [
            {
                'indicators' : [' ' ,' '],
                'subfields' : [
                    {
                        'code' : 'a',
                        'xref' : 777
                    }
                ]
            }
        ]
    }
    
    jbib3={
	"_id": 1161969,
	"000": ["00000nam a2200025#a 4500"],
	"001": ["1161969"],
	"008": ["180222s2017    usa    #r     |||1| eng d"],
	"029": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "JN"
				}, {
					"code": "b",
					"value": "N1741190 E"
				}
			]
		}
	],
	"039": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "DHU"
				}
			]
		}
	],
	"040": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "NNUN"
				}, {
					"code": "b",
					"value": "eng"
				}
			]
		}
	],
	"041": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "arachiengfrerusspa"
				}
			]
		}
	],
	"049": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "usa"
				}
			]
		}
	],
	"089": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "b",
					"value": "B03"
				}
			]
		}, {
			"indicators": [" ", " "],
			"subfields": [{
					"code": "b",
					"value": "B07"
				}
			]
		}
	],
	"091": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "GEN"
				}
			]
		}
	],
	"099": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "UNH"
				}, {
					"code": "b",
					"value": "DHU"
				}, {
					"code": "c",
					"value": "A(01)/R3"
				}, {
					"code": "q",
					"value": "A01R3"
				}
			]
		}
	],
	"191": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "A/72/PV.62"
				}, {
					"code": "b",
					"xref": 882332
				}, {
					"code": "c",
					"xref": 882332
				}, {
					"code": "9",
					"value": "G88"
				}, {
					"code": "q",
					"value": "A72PV62"
				}, {
					"code": "r",
					"value": "A72"
				}
			]
		}
	],
	"245": [{
			"indicators": ["1", "0"],
			"subfields": [{
					"code": "a",
					"value": "General Assembly official records, 72nd session :"
				}, {
					"code": "b",
					"value": "62nd plenary meeting, Monday, 4  December 2017, New York"
				}
			]
		}
	],
	"260": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "[New York] :"
				}, {
					"code": "b",
					"value": "UN,"
				}, {
					"code": "c",
					"value": "[2017]"
				}
			]
		}
	],
	"269": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "2017"
				}
			]
		}
	],
	"300": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "41 p."
				}
			]
		}
	],
	"495": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "GAOR, 72nd sess., Meeting records"
				}
			]
		}
	],
	"650": [{
			"indicators": ["1", "7"],
			"subfields": [{
					"code": "2",
					"value": "unbist"
				}, {
					"code": "a",
					"xref": 268584
				}
			]
		}
	],
	"793": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "PL"
				}
			]
		}
	],
	"930": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "UNDFE18"
				}
			]
		}
	],
	"981": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "General Assembly"
				}, {
					"code": "b",
					"value": "General Assembly Plenary"
				}
			]
		}
	],
	"989": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "Documents and Publications"
				}, {
					"code": "b",
					"value": "Meeting Records"
				}, {
					"code": "c",
					"value": "Verbatim Records"
				}
			]
		}
	],
	"991": [{
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884100
				}, {
					"code": "b",
					"xref": 884100
				}, {
					"code": "c",
					"xref": 884100
				}, {
					"code": "d",
					"xref": 884100
				}, {
					"code": "e",
					"value": "At the 62nd meeting, the Assembly took note of the report of the 1st Committee (A/72/399): decision 72/511"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884244
				}, {
					"code": "b",
					"xref": 884244
				}, {
					"code": "c",
					"xref": 884244
				}, {
					"code": "d",
					"xref": 884244
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution in A/72/400 (originally A/C.1/72/L.24) was adopted without vote: resolution 72/20"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884245
				}, {
					"code": "b",
					"xref": 884245
				}, {
					"code": "c",
					"xref": 884245
				}, {
					"code": "d",
					"xref": 884245
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution in A/72/401 (originally A/C.1/72/L.29) was adopted (132-3-46): resolution 72/21"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884246
				}, {
					"code": "b",
					"xref": 884246
				}, {
					"code": "c",
					"xref": 884246
				}, {
					"code": "d",
					"xref": 884246
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution in A/72/402 (originally A/C.1/72/L.37) was adopted without vote: resolution 72/22"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884247
				}, {
					"code": "b",
					"xref": 884247
				}, {
					"code": "c",
					"xref": 884247
				}, {
					"code": "d",
					"xref": 884247
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution in A/72/403 (originally A/C.1/72/L.9) was adopted (180-3-0): resolution 72/23"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884248
				}, {
					"code": "b",
					"xref": 884248
				}, {
					"code": "c",
					"xref": 884248
				}, {
					"code": "d",
					"xref": 884248
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft decision in A/72/404 (originally A/C.1/72/L.44 was adopted (185-0-1): decision 72/512"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884249
				}, {
					"code": "b",
					"xref": 884249
				}, {
					"code": "c",
					"xref": 884249
				}, {
					"code": "d",
					"xref": 884249
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution in A/72/405 (originally A/C.1/72/L.1) was adopted without vote: resolution 72/24"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884250
				}, {
					"code": "b",
					"xref": 884250
				}, {
					"code": "c",
					"xref": 884250
				}, {
					"code": "d",
					"xref": 884250
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution in A/72/406 (originally A/C.1/72/L.10/Rev.1) was adopted (125-0-62): resolution 72/25"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884252
				}, {
					"code": "b",
					"xref": 884252
				}, {
					"code": "c",
					"xref": 884252
				}, {
					"code": "d",
					"xref": 884252
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution I in A/72/407 (originally A/C.1/72/L.3) was adopted (182-0-3): resolution 72/26"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884253
				}, {
					"code": "b",
					"xref": 884253
				}, {
					"code": "c",
					"xref": 884253
				}, {
					"code": "d",
					"xref": 884253
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution II in A/72/407 (originally A/C.1/72/L.53) was adopted (131-4-48): resolution 72/27"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884254
				}, {
					"code": "b",
					"xref": 884254
				}, {
					"code": "c",
					"xref": 884254
				}, {
					"code": "d",
					"xref": 884254
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution in A/72/408 (originally A/C.1/72/L.52/Rev.1) was adopted without vote: resolution 72/28"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884277
				}, {
					"code": "b",
					"xref": 884277
				}, {
					"code": "c",
					"xref": 884277
				}, {
					"code": "d",
					"xref": 884277
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution I in A/72/409 (originally A/C.1/72/L.4) was adopted (118-44-17): resolution 72/29"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884285
				}, {
					"code": "b",
					"xref": 884285
				}, {
					"code": "c",
					"xref": 884285
				}, {
					"code": "d",
					"xref": 884285
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution II in A/72/409 (originally A/C.1/72/L.5) was adopted (141-15-27): resolution 72/30"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884282
				}, {
					"code": "b",
					"xref": 884282
				}, {
					"code": "c",
					"xref": 884282
				}, {
					"code": "d",
					"xref": 884282
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution III in A/72/409 (originally A/C.1/72/L.6) was adopted (125-39-14): resolution 72/31"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884281
				}, {
					"code": "b",
					"xref": 884281
				}, {
					"code": "c",
					"xref": 884281
				}, {
					"code": "d",
					"xref": 884281
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution IV in A/72/409 (originally A/C.1/72/L.7) was adopted (173-1-11): resolution 72/32"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884535
				}, {
					"code": "b",
					"xref": 884535
				}, {
					"code": "c",
					"xref": 884535
				}, {
					"code": "d",
					"xref": 884535
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution V in A/72/409 (originally A/C.1/72/L.11) was adopted without vote: resolution 72/33"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884263
				}, {
					"code": "b",
					"xref": 884263
				}, {
					"code": "c",
					"xref": 884263
				}, {
					"code": "d",
					"xref": 884263
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution VI in A/72/409 (originally A/C.1/72/L.12) was adopted without vote: resolution 72/34"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884261
				}, {
					"code": "b",
					"xref": 884261
				}, {
					"code": "c",
					"xref": 884261
				}, {
					"code": "d",
					"xref": 884261
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution VII in A/72/409 (originally A/C.1/72/L.13/Rev.1) was adopted (184-1-2): resolution 72/35"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884284
				}, {
					"code": "b",
					"xref": 884284
				}, {
					"code": "c",
					"xref": 884284
				}, {
					"code": "d",
					"xref": 884284
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution VIII in A/72/409 (originally A/C.1/72/L.15/Rev.1) was adopted without vote: resolution 72/36"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884287
				}, {
					"code": "b",
					"xref": 884287
				}, {
					"code": "c",
					"xref": 884287
				}, {
					"code": "d",
					"xref": 884287
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution IX in A/72/409 (originally A/C.1/72/L.17) was adopted (130-36-15): resolution 72/37"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884257
				}, {
					"code": "b",
					"xref": 884257
				}, {
					"code": "c",
					"xref": 884257
				}, {
					"code": "d",
					"xref": 884257
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution X in A/72/409 (originally A/C.1/72/L.18) was adopted (119-41-20): resolution 72/38"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884272
				}, {
					"code": "b",
					"xref": 884272
				}, {
					"code": "c",
					"xref": 884272
				}, {
					"code": "d",
					"xref": 884272
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XI in A/72/409 (originally A/C.1/72/L.19) was adopted (137-31-16): resolution 72/39"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884269
				}, {
					"code": "b",
					"xref": 884269
				}, {
					"code": "c",
					"xref": 884269
				}, {
					"code": "d",
					"xref": 884269
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XII in A/72/409 (originally A/C.1/72/L.21) was adopted without vote: resolution 72/40"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884270
				}, {
					"code": "b",
					"xref": 884270
				}, {
					"code": "c",
					"xref": 884270
				}, {
					"code": "d",
					"xref": 884270
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XIII in A/72/409 (originally A/C.1/72/L.22) was adopted (124-49-11): resolution 72/41"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884274
				}, {
					"code": "b",
					"xref": 884274
				}, {
					"code": "c",
					"xref": 884274
				}, {
					"code": "d",
					"xref": 884274
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XIV in A/72/409 (originally A/C.1/72/L.23) was adopted without vote: resolution 72/42"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884267
				}, {
					"code": "b",
					"xref": 884267
				}, {
					"code": "c",
					"xref": 884267
				}, {
					"code": "d",
					"xref": 884267
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XV in A/72/409 (originally A/C.1/72/L.26/Rev.1) was adopted (159-7-14): resolution 72/43"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884278
				}, {
					"code": "b",
					"xref": 884278
				}, {
					"code": "c",
					"xref": 884278
				}, {
					"code": "d",
					"xref": 884278
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XVI in A/72/409 (originally A/C.1/72/L.27) was adopted (155-0-29): resolution 72/44"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884264
				}, {
					"code": "b",
					"xref": 884264
				}, {
					"code": "c",
					"xref": 884264
				}, {
					"code": "d",
					"xref": 884264
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XVII in A/72/409 (originally A/C.1/72/L.28) was adopted (149-5-29): resolution 72/45"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884259
				}, {
					"code": "b",
					"xref": 884259
				}, {
					"code": "c",
					"xref": 884259
				}, {
					"code": "d",
					"xref": 884259
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XVIII in A/72/409 (originally A/C.1/72/L.30) was adopted without vote: resolution 72/46"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884265
				}, {
					"code": "b",
					"xref": 884265
				}, {
					"code": "c",
					"xref": 884265
				}, {
					"code": "d",
					"xref": 884265
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XIX in A/72/409 (originally A/C.1/72/L.31) was adopted without vote: resolution 72/47"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884273
				}, {
					"code": "b",
					"xref": 884273
				}, {
					"code": "c",
					"xref": 884273
				}, {
					"code": "d",
					"xref": 884273
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XX in A/72/409 (originally A/C.1/72/L.32) was adopted (130-4-51): resolution 72/48"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884262
				}, {
					"code": "b",
					"xref": 884262
				}, {
					"code": "c",
					"xref": 884262
				}, {
					"code": "d",
					"xref": 884262
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XXI in A/72/409 (originally A/C.1/72/L.33) was adopted (181-0-3): resolution 72/49"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884280
				}, {
					"code": "b",
					"xref": 884280
				}, {
					"code": "c",
					"xref": 884280
				}, {
					"code": "d",
					"xref": 884280
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XXII in A/72/409 (originally A/C.1/72/L.35) was adopted (156-4-24): resolution 72/50"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884255
				}, {
					"code": "b",
					"xref": 884255
				}, {
					"code": "c",
					"xref": 884255
				}, {
					"code": "d",
					"xref": 884255
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XXIII in A/72/409 (originally A/C.1/72/L.36) was adopted without vote: resolution 72/51"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884260
				}, {
					"code": "b",
					"xref": 884260
				}, {
					"code": "c",
					"xref": 884260
				}, {
					"code": "d",
					"xref": 884260
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XXIV in A/72/409 (originally A/C.1/72/L.38) was adopted without vote: resolution 72/52"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884268
				}, {
					"code": "b",
					"xref": 884268
				}, {
					"code": "c",
					"xref": 884268
				}, {
					"code": "d",
					"xref": 884268
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XXV in A/72/409 (originally A/C.1/72/L.40) was adopted (167-0-17): resolution 72/53"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884288
				}, {
					"code": "b",
					"xref": 884288
				}, {
					"code": "c",
					"xref": 884288
				}, {
					"code": "d",
					"xref": 884288
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XXVI in A/72/409 (originally A/C.1/72/L.41) was adopted (142-2-36): resolution 72/54"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884275
				}, {
					"code": "b",
					"xref": 884275
				}, {
					"code": "c",
					"xref": 884275
				}, {
					"code": "d",
					"xref": 884275
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XXVII in A/72/409 (originally A/C.1/72/L.43) was adopted without vote: resolution 72/55"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884276
				}, {
					"code": "b",
					"xref": 884276
				}, {
					"code": "c",
					"xref": 884276
				}, {
					"code": "d",
					"xref": 884276
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XXIX in A/72/409 (originally A/C.1/72/L.46) was adopted without vote: resolution 72/56"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884271
				}, {
					"code": "b",
					"xref": 884271
				}, {
					"code": "c",
					"xref": 884271
				}, {
					"code": "d",
					"xref": 884271
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XXX in A/72/409 (originally A/C.1/72/L.56/Rev.1) was adopted without vote: resolution 72/57"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884266
				}, {
					"code": "b",
					"xref": 884266
				}, {
					"code": "c",
					"xref": 884266
				}, {
					"code": "d",
					"xref": 884266
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution XXXI in A/72/409 (originally A/C.1/72/L.57) was adopted (131-31-18): resolution 72/58"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884256
				}, {
					"code": "b",
					"xref": 884256
				}, {
					"code": "c",
					"xref": 884256
				}, {
					"code": "d",
					"xref": 884256
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft decision I in A/72/409 (originally A/C.1/72/L.50) was adopted (182-1-4): decision 72/513"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884289
				}, {
					"code": "b",
					"xref": 884289
				}, {
					"code": "c",
					"xref": 884289
				}, {
					"code": "d",
					"xref": 884289
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft decision II in A/72/409 (originally A/C.1/72/L.55) was adopted without vote: decision 72/514"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884279
				}, {
					"code": "b",
					"xref": 884279
				}, {
					"code": "c",
					"xref": 884279
				}, {
					"code": "d",
					"xref": 884279
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft decision III in A/72/409 (originally A/C.1/72/L.58) was adopted without vote: decision 72/515"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884291
				}, {
					"code": "b",
					"xref": 884291
				}, {
					"code": "c",
					"xref": 884291
				}, {
					"code": "d",
					"xref": 884291
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution I in A/72/410 (originally A/C.1/72/L.47) was adopted (123-50-10): resolution 72/59"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884292
				}, {
					"code": "b",
					"xref": 884292
				}, {
					"code": "c",
					"xref": 884292
				}, {
					"code": "d",
					"xref": 884292
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution II in A/72/410 (originally A/C.1/72/L.39) was adopted without vote: resolution 72/60"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884293
				}, {
					"code": "b",
					"xref": 884293
				}, {
					"code": "c",
					"xref": 884293
				}, {
					"code": "d",
					"xref": 884293
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution III in A/72/410 (originally A/C.1/72/L.51) was adopted without vote: resolution 72/61"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884294
				}, {
					"code": "b",
					"xref": 884294
				}, {
					"code": "c",
					"xref": 884294
				}, {
					"code": "d",
					"xref": 884294
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution IV in A/72/410 (originally A/C.1/72/L.48) was adopted without vote: resolution 72/62"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884295
				}, {
					"code": "b",
					"xref": 884295
				}, {
					"code": "c",
					"xref": 884295
				}, {
					"code": "d",
					"xref": 884295
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution V in A/72/410 (originally A/C.1/72/L.20) was adopted without vote: resolution 72/63"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884296
				}, {
					"code": "b",
					"xref": 884296
				}, {
					"code": "c",
					"xref": 884296
				}, {
					"code": "d",
					"xref": 884296
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution VI in A/72/410 (originally A/C.1/72/L.34) was adopted without vote: resolution 72/64"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884298
				}, {
					"code": "b",
					"xref": 884298
				}, {
					"code": "c",
					"xref": 884298
				}, {
					"code": "d",
					"xref": 884298
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution I in A/72/411 (originally A/C.1/72/L.14) was adopted without vote: resolution 72/65"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884299
				}, {
					"code": "b",
					"xref": 884299
				}, {
					"code": "c",
					"xref": 884299
				}, {
					"code": "d",
					"xref": 884299
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution II in A/72/411 (originally A/C.1/72/L.25) was adopted without vote: resolution 72/66"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884300
				}, {
					"code": "b",
					"xref": 884300
				}, {
					"code": "c",
					"xref": 884300
				}, {
					"code": "d",
					"xref": 884300
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution in A/72/412 (originally A/C.1/72/L.2) was adopted (157-5-20): resolution 72/67"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884301
				}, {
					"code": "b",
					"xref": 884301
				}, {
					"code": "c",
					"xref": 884301
				}, {
					"code": "d",
					"xref": 884301
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution in A/72/413 (originally A/C.1/72/L.16/Rev.1) was adopted without vote: resolution 72/68"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884302
				}, {
					"code": "b",
					"xref": 884302
				}, {
					"code": "c",
					"xref": 884302
				}, {
					"code": "d",
					"xref": 884302
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution in A/72/414 (originally A/C.1/72/L.8) was adopted without vote: resolution 72/69"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884303
				}, {
					"code": "b",
					"xref": 884303
				}, {
					"code": "c",
					"xref": 884303
				}, {
					"code": "d",
					"xref": 884303
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution in A/72/415 (originally A/C.1/72/L.42) was adopted (180-1-4): resolution 72/70"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884304
				}, {
					"code": "b",
					"xref": 884304
				}, {
					"code": "c",
					"xref": 884304
				}, {
					"code": "d",
					"xref": 884304
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft resolution in A/72/416 (originally A/C.1/72/L.49) was adopted without vote: resolution 72/71"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884344
				}, {
					"code": "b",
					"xref": 884344
				}, {
					"code": "c",
					"xref": 884344
				}, {
					"code": "d",
					"xref": 884344
				}, {
					"code": "e",
					"value": "At the 62nd meeting, draft decision in A/72/478 entitled \"Provisional programme of work and timetable of the 1st Committee for 2018\" was adopted without vote: decision 72/516"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}, {
			"indicators": ["1", " "],
			"subfields": [{
					"code": "a",
					"xref": 884403
				}, {
					"code": "b",
					"xref": 884403
				}, {
					"code": "c",
					"xref": 884403
				}, {
					"code": "d",
					"xref": 884403
				}, {
					"code": "e",
					"value": "At the 62nd meeting, the Assembly took note of the report of the 1st Committee (A/72/483): decision 72/517"
				}, {
					"code": "z",
					"value": "I"
				}
			]
		}
	],
	"992": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "2017-12-04"
				}
			]
		}
	],
	"998": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "20180222075600"
				}, {
					"code": "b",
					"value": "pnser"
				}, {
					"code": "c",
					"value": "20190715122000"
				}, {
					"code": "d",
					"value": "vwcat2"
				}, {
					"code": "x",
					"value": "0x00010000be3addb5"
				}, {
					"code": "z",
					"value": "20190715162125"
				}
			]
		}
	],
	"999": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "pnq20180222"
				}, {
					"code": "b",
					"value": "20180222"
				}, {
					"code": "c",
					"value": "q"
				}
			]
		}, {
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "vvc20180222"
				}, {
					"code": "b",
					"value": "20180222"
				}, {
					"code": "c",
					"value": "c"
				}
			]
		}, {
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "vvr20180223"
				}, {
					"code": "b",
					"value": "20180223"
				}, {
					"code": "c",
					"value": "r"
				}
			]
		}, {
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "vwt20190226"
				}, {
					"code": "b",
					"value": "20190226"
				}, {
					"code": "c",
					"value": "t"
				}
			]
		}, {
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "vwu20190715"
				}, {
					"code": "b",
					"value": "20190715"
				}, {
					"code": "c",
					"value": "u"
				}
			]
		}
	]
}





    jauth = {
        '_id' : 777,
        '150' : [
            {
                'indicators' : [' ', ' '],
                'subfields' : [
                    {
                        'code' : 'a',
                        'value' : 'header text'
                    }
                ]
            }
        ]
    }
    
    jauth2 = {
        '_id' : 333,
        '150' : [
            {
                'indicators' : [' ', ' '],
                'subfields' : [
                    {
                        'code' : 'a',
                        'value' : 'another header'
                    }
                ]
            }
        ]
    }

    jauth3= {
	"_id": 882332,
	"000": ["00000nz  a2200025n  4500"],
	"001": ["882332"],
	"008": ["170113nn annzbbban           n ana     d"],
	"035": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "S0000053"
				}
			]
		}
	],
	"040": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "NNUN"
				}, {
					"code": "b",
					"value": "eng"
				}, {
					"code": "f",
					"value": "unbisn"
				}
			]
		}
	],
	"046": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "s",
					"value": "201709"
				}, {
					"code": "t",
					"value": "201809"
				}
			]
		}
	],
	"190": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "b",
					"value": "A/"
				}, {
					"code": "c",
					"value": "72"
				}
			]
		}
	],
	"370": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "e",
					"value": "New York"
				}
			]
		}
	],
	"905": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "DHL"
				}
			]
		}
	],
	"925": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "UN. General Assembly (72nd sess. : 2017-2018)"
				}
			]
		}
	],
	"998": [{
			"indicators": [" ", " "],
			"subfields": [{
					"code": "a",
					"value": "20170113141000"
				}, {
					"code": "b",
					"value": "bccat"
				}, {
					"code": "c",
					"value": "20170117082600"
				}, {
					"code": "d",
					"value": "pacat"
				}, {
					"code": "x",
					"value": "0x00010000be4258f2"
				}, {
					"code": "z",
					"value": "20190719134206"
				}
			]
		}
	]
}

    
    invalid = {
        '_id' : 'string invalid',
        '150' : [
            {
                'indicators' : [' ', ' '],
                'subfields' : [
                    {
                        'code' : 'a',
                        'value' : 'header text'
                    }
                ]
            }
        ]
    }    


#bibs=Bib.match_id(1161969)
#for bib in bibs:
#print(Bib.match_id(1161969).get_values("991"))
	        
#for field in Bib.match_id(1161969).get_fields('991'):
#    for subfield in field.subfields:
#        print(Bib.serialize_subfield(subfield))
		
class Todo(TestCase):
   def setUp(self):
        #DB.connect('mongodb://.../?authSource=dummy',mock=True)
        #Bib(Data.jbib).commit()

    def test_e(self):
        # test utility methods
        #todo
        pass
        
    def test_f(self):
        # test serializations
        #todo
        pass
        
    def test_g(self):
        # test de-serializations
        #todo
        pass

class To_itpp(TestCase):
    pass
    
    #def test_proper_dict(self):
    #    bib = Bib.match_id(1161969)
    #    self.assertEqual(type((bib.to_itpp()).get("245")),"dict")
    #
    #def test_proper_list_repetitive_field_values(self):
    #    bib = Bib.match_id(1161969)
    #    self.assertEqual(type((bib.to_itpp()).get("991")),"list")
    #
    #def test_correct_list_repetitive_field_values(self):
    #    bib = Bib.match_id(1161969)
    #    self.assertEqual(len((bib.to_itpp()).get("991")),64)
    #
    #def test_proper_dict2(self):
    #    bib = Bib.match_id(1161969)
    #    self.assertEqual(len((bib.to_itpp()).get("245")),2)
    #
    #def test_245(self):
    #    bib = Bib.match_id(1161969)
    #    self.assertEqual(((bib.to_itpp()).get("245").get("a")),"General Assembly official records, 72nd session :")
    #    self.assertEqual(((bib.to_itpp()).get("245").get("b")),"62nd plenary meeting, Monday, 4  December 2017, New York")
    #    #self.assertEqual(getattr(getattr(bib.to_itpp(),"245"),"c"),"title")

    
    
