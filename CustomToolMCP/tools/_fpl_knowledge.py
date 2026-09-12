# -*- coding: utf-8 -*-
"""exp27 지식 모듈 — 지문 16종 + 정답지 + 대조기 (자동 생성: tests/s2_build_knowledge.py).
파일명이 _ 로 시작하므로 CustomToolMCP 서버 발견에서 제외된다(데이터 모듈 — MCP 도구 아님).
수동 편집 금지 — 생성기를 다시 돌려라. 원천: exp26 연구 실측(정확 일치 검증 완료).

지문 대조 등급:
  1 = 완전 일치(수량 9종 + 주기 + 시작 타이밍) → 정답지 경로 재생 (병렬 OFF·LLM 0회)
  2 = 수량 일치·조건 상이(주기/타이밍 다름) → LLM 강화 입력(최강 이웃 + 차이 명시)
  3 = 신규 → 2팔 병렬
"""
TOL = {'period': 0.001, 'wns': 0.005, 'tns': 2.0}

def parse_fingerprint(text):
    """진단 출력의 FPL_FP_* 줄에서 지문 dict 추출. 실패 항목은 None."""
    import re
    fp = {'qty': {}, 'period': None, 'wns': None, 'tns': None, 'failing': None}
    m = re.search(r'FPL_FP_QTY: (.+)', text or '')
    if m:
        for kv in m.group(1).split():
            k, v = kv.split('=')
            try: fp['qty'][k] = int(v)
            except ValueError: pass
    m = re.search(r'FPL_FP_CLK: period=([\d.]+)', text or '')
    if m: fp['period'] = float(m.group(1))
    m = re.search(r'FPL_FP_TIMING: wns=(-?[\d.]+) tns=(-?[\d.]+) failing=(\d+)', text or '')
    if m:
        fp['wns'], fp['tns'], fp['failing'] = float(m.group(1)), float(m.group(2)), int(m.group(3))
    return fp

def match_fingerprint(fp):
    """(grade, design, diffs) — grade 1/2/3. 수량 벡터는 16종 간 유일함이 생성기에서 검증됨."""
    qty = fp.get('qty') or {}
    for d, ref in FINGERPRINTS.items():
        if all(qty.get(k) == v for k, v in ref['qty'].items()):
            diffs = []
            if fp.get('period') is None or abs(fp['period'] - ref['period']) > TOL['period']:
                diffs.append(('period', fp.get('period'), ref['period']))
            if fp.get('wns') is None or abs(fp['wns'] - ref['wns']) > TOL['wns']:
                diffs.append(('wns', fp.get('wns'), ref['wns']))
            if fp.get('tns') is None or abs(fp['tns'] - ref['tns']) > TOL['tns']:
                diffs.append(('tns', fp.get('tns'), ref['tns']))
            if fp.get('failing') != ref['failing']:
                diffs.append(('failing', fp.get('failing'), ref['failing']))
            return (1 if not diffs else 2), d, diffs
    return 3, None, []

def giant_directive(lut, matched_design=None):
    """exp29 항목1 (승인 8/9): F-E(Explore) 고정 — 정답지·규칙(>=260k Default) 분기 제거.
    프레임워크는 이 함수를 더 이상 호출하지 않는다(호출부 하드코딩) — 기록·시험용 잔존."""
    return 'Explore', 'fixed-F-E'

FINGERPRINTS = {
 "3d": {
  "qty": {
   "lut": 13869,
   "ff": 5356,
   "dsp": 3,
   "bram36": 0,
   "bram18": 0,
   "carry": 246,
   "uram": 0,
   "macro": 0,
   "endpoints": 105240
  },
  "period": 1.538,
  "wns": -2.153,
  "tns": -53058.883,
  "failing": 86488
 },
 "amd": {
  "qty": {
   "lut": 3181,
   "ff": 4482,
   "dsp": 40,
   "bram36": 10,
   "bram18": 4,
   "carry": 272,
   "uram": 0,
   "macro": 0,
   "endpoints": 14547
  },
  "period": 1.57,
  "wns": -1.686,
  "tns": -2843.377,
  "failing": 4887
 },
 "boom_soc": {
  "qty": {
   "lut": 226568,
   "ff": 97744,
   "dsp": 61,
   "bram36": 153,
   "bram18": 16,
   "carry": 1434,
   "uram": 0,
   "macro": 0,
   "endpoints": 247052
  },
  "period": 1.569,
  "wns": -19.162,
  "tns": -1676733.375,
  "failing": 217988
 },
 "boom_v2": {
  "qty": {
   "lut": 229627,
   "ff": 98119,
   "dsp": 61,
   "bram36": 153,
   "bram18": 16,
   "carry": 1434,
   "uram": 0,
   "macro": 0,
   "endpoints": 247479
  },
  "period": 1.569,
  "wns": -11.392,
  "tns": -1084199.5,
  "failing": 220131
 },
 "corescore": {
  "qty": {
   "lut": 99972,
   "ff": 119833,
   "dsp": 0,
   "bram36": 0,
   "bram18": 500,
   "carry": 2,
   "uram": 0,
   "macro": 0,
   "endpoints": 227802
  },
  "period": 1.6667,
  "wns": -1.238,
  "tns": -7537.547,
  "failing": 39008
 },
 "digit": {
  "qty": {
   "lut": 22535,
   "ff": 23430,
   "dsp": 0,
   "bram36": 160,
   "bram18": 1,
   "carry": 401,
   "uram": 4,
   "macro": 0,
   "endpoints": 62728
  },
  "period": 1.7,
  "wns": -1.025,
  "tns": -8964.492,
  "failing": 22946
 },
 "finn": {
  "qty": {
   "lut": 73649,
   "ff": 45800,
   "dsp": 0,
   "bram36": 16,
   "bram18": 17,
   "carry": 5851,
   "uram": 0,
   "macro": 0,
   "endpoints": 100228
  },
  "period": 1.6,
  "wns": -1.91,
  "tns": -27895.215,
  "failing": 46438
 },
 "fir": {
  "qty": {
   "lut": 603,
   "ff": 7438,
   "dsp": 456,
   "bram36": 0,
   "bram18": 0,
   "carry": 12,
   "uram": 0,
   "macro": 0,
   "endpoints": 36615
  },
  "period": 2.5,
  "wns": -0.313,
  "tns": -56.458,
  "failing": 252
 },
 "ispd16": {
  "qty": {
   "lut": 289437,
   "ff": 233935,
   "dsp": 200,
   "bram36": 384,
   "bram18": 0,
   "carry": 0,
   "uram": 0,
   "macro": 0,
   "endpoints": 343811
  },
  "period": 1.538,
  "wns": -7.752,
  "tns": -613731.062,
  "failing": 242906
 },
 "logicnets": {
  "qty": {
   "lut": 30839,
   "ff": 1660,
   "dsp": 0,
   "bram36": 0,
   "bram18": 0,
   "carry": 0,
   "uram": 0,
   "macro": 0,
   "endpoints": 1540
  },
  "period": 1.5,
  "wns": -0.978,
  "tns": -835.005,
  "failing": 1529
 },
 "optical": {
  "qty": {
   "lut": 33803,
   "ff": 36740,
   "dsp": 42,
   "bram36": 57,
   "bram18": 8,
   "carry": 2960,
   "uram": 1,
   "macro": 0,
   "endpoints": 86413
  },
  "period": 2.0,
  "wns": -1.078,
  "tns": -1515.246,
  "failing": 7866
 },
 "spam": {
  "qty": {
   "lut": 5361,
   "ff": 13117,
   "dsp": 224,
   "bram36": 1,
   "bram18": 4,
   "carry": 251,
   "uram": 0,
   "macro": 0,
   "endpoints": 81122
  },
  "period": 1.6,
  "wns": -0.686,
  "tns": -831.866,
  "failing": 6786
 },
 "vexriscv": {
  "qty": {
   "lut": 1906,
   "ff": 1199,
   "dsp": 4,
   "bram36": 3,
   "bram18": 6,
   "carry": 48,
   "uram": 0,
   "macro": 0,
   "endpoints": 3550
  },
  "period": 1.57,
  "wns": -1.654,
  "tns": -671.139,
  "failing": 1937
 },
 "vexriscv_v2": {
  "qty": {
   "lut": 2113,
   "ff": 1678,
   "dsp": 4,
   "bram36": 1,
   "bram18": 5,
   "carry": 47,
   "uram": 0,
   "macro": 0,
   "endpoints": 5079
  },
  "period": 1.57,
  "wns": -0.946,
  "tns": -1023.873,
  "failing": 2933
 },
 "vtr_mcml": {
  "qty": {
   "lut": 43311,
   "ff": 15228,
   "dsp": 105,
   "bram36": 140,
   "bram18": 4,
   "carry": 3949,
   "uram": 0,
   "macro": 0,
   "endpoints": 37824
  },
  "period": 1.538,
  "wns": -14.527,
  "tns": -107570.352,
  "failing": 27003
 },
 "vtr_v2": {
  "qty": {
   "lut": 45700,
   "ff": 15535,
   "dsp": 105,
   "bram36": 140,
   "bram18": 4,
   "carry": 3949,
   "uram": 0,
   "macro": 0,
   "endpoints": 38103
  },
  "period": 1.538,
  "wns": -12.885,
  "tns": -70807.555,
  "failing": 18773
 }
}

ANSWER_SHEET = {
 "3d": {
  "kind": "mid",
  "variant": "A",
  "steps": [
   [
    "G1",
    "F-N",
    2102,
    29.461
   ]
  ],
  "overhead_s": 93,
  "expect_alpha": 29.461,
  "expect_minutes": 36.6,
  "expect_utility": 27.664,
  "source": "exp26 research 재계산(utility-최적·60분 이내)"
 },
 "amd": {
  "kind": "mid",
  "variant": "C",
  "steps": [
   [
    "G1",
    "C-D",
    312,
    99.544
   ],
   [
    "G2",
    "F-D",
    403,
    102.207
   ]
  ],
  "overhead_s": 83,
  "expect_alpha": 102.207,
  "expect_minutes": 13.3,
  "expect_utility": 99.941,
  "source": "exp26 research 재계산(utility-최적·60분 이내)"
 },
 "corescore": {
  "kind": "mid",
  "variant": "A",
  "steps": [
   [
    "G1",
    "C-D",
    2076,
    97.657
   ]
  ],
  "overhead_s": 231,
  "expect_alpha": 97.657,
  "expect_minutes": 38.4,
  "expect_utility": 91.4,
  "source": "exp26 research 재계산(utility-최적·60분 이내)"
 },
 "digit": {
  "kind": "mid",
  "variant": "D",
  "steps": [
   [
    "G1",
    "F-D",
    1074,
    54.435
   ],
   [
    "G2",
    "F-E",
    1266,
    59.649
   ],
   [
    "RD",
    "route_directive",
    502,
    61.11
   ]
  ],
  "overhead_s": 106,
  "expect_alpha": 61.11,
  "expect_minutes": 49.7,
  "expect_utility": 56.048,
  "source": "exp26 research 재계산(utility-최적·60분 이내)"
 },
 "finn": {
  "kind": "mid",
  "variant": "A",
  "steps": [
   [
    "G1",
    "F-E",
    1953,
    66.717
   ]
  ],
  "overhead_s": 161,
  "expect_alpha": 66.717,
  "expect_minutes": 35.2,
  "expect_utility": 62.8,
  "source": "exp26 research 재계산(utility-최적·60분 이내)"
 },
 "fir": {
  "kind": "mid",
  "variant": "A",
  "steps": [
   [
    "G1",
    "F-E",
    724,
    22.009
   ]
  ],
  "overhead_s": 110,
  "expect_alpha": 22.009,
  "expect_minutes": 13.4,
  "expect_utility": 21.517,
  "source": "exp26 research 재계산(utility-최적·60분 이내)",
  "note": "G1은 실험 기록상 C-D(EWIDE 우회로)였으나 동일 작업인 명시적 F-E로 지정(α 22.01 동일)"
 },
 "logicnets": {
  "kind": "mid",
  "variant": "E",
  "steps": [
   [
    "G1",
    "C-E",
    1060,
    118.915
   ],
   [
    "RD",
    "route_directive",
    386,
    121.383
   ]
  ],
  "overhead_s": 98,
  "expect_alpha": 121.383,
  "expect_minutes": 25.7,
  "expect_utility": 116.179,
  "source": "exp26 research 재계산(utility-최적·60분 이내)"
 },
 "optical": {
  "kind": "mid",
  "variant": "A",
  "steps": [
   [
    "G1",
    "C-D",
    1139,
    34.18
   ]
  ],
  "overhead_s": 116,
  "expect_alpha": 34.18,
  "expect_minutes": 20.9,
  "expect_utility": 32.988,
  "source": "exp26 research 재계산(utility-최적·60분 이내)"
 },
 "spam": {
  "kind": "mid",
  "variant": "E",
  "steps": [
   [
    "G1",
    "C-D",
    1430,
    27.887
   ],
   [
    "RD",
    "route_directive",
    548,
    29.19
   ]
  ],
  "overhead_s": 106,
  "expect_alpha": 29.19,
  "expect_minutes": 34.7,
  "expect_utility": 27.5,
  "source": "exp26 research 재계산(utility-최적·60분 이내)"
 },
 "vexriscv": {
  "kind": "mid",
  "variant": "C",
  "steps": [
   [
    "G1",
    "C-N",
    752,
    157.772
   ],
   [
    "G2",
    "F-D",
    831,
    179.782
   ]
  ],
  "overhead_s": 73,
  "expect_alpha": 179.782,
  "expect_minutes": 27.6,
  "expect_utility": 171.512,
  "source": "exp26 research 재계산(utility-최적·60분 이내)"
 },
 "vexriscv_v2": {
  "kind": "mid",
  "variant": "C",
  "steps": [
   [
    "G1",
    "C-D",
    696,
    32.097
   ],
   [
    "G2",
    "F-N",
    1514,
    41.718
   ]
  ],
  "overhead_s": 76,
  "expect_alpha": 41.718,
  "expect_minutes": 38.1,
  "expect_utility": 39.069,
  "source": "exp26 research 재계산(utility-최적·60분 이내)"
 },
 "vtr_mcml": {
  "kind": "mid",
  "variant": "A",
  "steps": [
   [
    "G1",
    "C-N",
    3040,
    16.898
   ]
  ],
  "overhead_s": 135,
  "expect_alpha": 16.898,
  "expect_minutes": 52.9,
  "expect_utility": 15.408,
  "source": "exp26 research 재계산(utility-최적·60분 이내)"
 },
 "vtr_v2": {
  "kind": "mid",
  "variant": "A",
  "steps": [
   [
    "G1",
    "F-N",
    3084,
    4.402
   ]
  ],
  "overhead_s": 132,
  "expect_alpha": 4.402,
  "expect_minutes": 53.6,
  "expect_utility": 4.009,
  "source": "exp26 research 재계산(utility-최적·60분 이내)"
 },
 "ispd16": {
  "kind": "giant",
  "directive": "Default",
  "finish": "route_only",
  "expect_wns": -3.192,
  "est_s": 2343,
  "source": "8/1 인스턴스 1단계 실측: place+route 2343s WNS −3.192 (2단계 −3.224와 품질 동급)"
 },
 "boom_soc": {
  "kind": "giant",
  "directive": "Default",
  "finish": "route_only",
  "expect_wns": -11.392,
  "est_s": 2238,
  "source": "8/1 인스턴스 2단계 실측 −11.392/37.3m (Explore −11.507) — 1단계 직접 실측 없음, 동급 예상(실험2: 기본 phys_opt 기여≈0). 현행 규칙(<260k→Explore)과 다른 실측 지시자"
 },
 "boom_v2": {
  "kind": "giant",
  "directive": "Explore",
  "finish": "route_only",
  "expect_wns": -9.24,
  "est_s": 1896,
  "source": "8/1 인스턴스 2단계 실측 −9.240/31.6m — 1단계 직접 실측 없음, 동급 예상(실험2 근거)"
 }
}

G1_CATALOG = {
 "3d": {
  "metrics": {
   "cr_mean": 1.68,
   "route_ratio": 77.628,
   "lut": 13869,
   "spread": 65.8,
   "high_fanout": 1,
   "wns": -2.153
  },
  "actions": {
   "C-D": {
    "alpha": 0.0,
    "min": 23.4
   },
   "C-N": {
    "alpha": 19.6,
    "min": 35.1
   },
   "C-E": {
    "alpha": 0.0,
    "min": 24.4
   },
   "F-D": {
    "alpha": 10.84,
    "min": 26.8
   },
   "F-N": {
    "alpha": 29.46,
    "min": 34.3
   },
   "F-E": {
    "alpha": 6.54,
    "min": 23.7
   }
  }
 },
 "amd": {
  "metrics": {
   "cr_mean": 1.82,
   "route_ratio": 87.502,
   "lut": 3181,
   "spread": 56.9,
   "high_fanout": 4,
   "wns": -1.686
  },
  "actions": {
   "C-D": {
    "alpha": 99.54,
    "min": 7.4
   },
   "C-N": {
    "alpha": 98.55,
    "min": 11.7
   },
   "C-E": {
    "alpha": 95.94,
    "min": 7.0
   },
   "F-D": {
    "alpha": 97.08,
    "min": 7.2
   },
   "F-N": {
    "alpha": 94.97,
    "min": 9.1
   },
   "F-E": {
    "alpha": 97.08,
    "min": 5.6
   }
  }
 },
 "corescore": {
  "metrics": {
   "cr_mean": 1.22,
   "route_ratio": 51.489,
   "lut": 99972,
   "spread": 232.4,
   "high_fanout": 0,
   "wns": -1.238
  },
  "actions": {
   "C-D": {
    "alpha": 97.66,
    "min": 37.6
   },
   "C-N": {
    "alpha": 95.91,
    "min": 47.2
   },
   "C-E": {
    "alpha": 92.45,
    "min": 38.4
   },
   "F-D": {
    "alpha": 6.15,
    "min": 28.5
   },
   "F-N": {
    "alpha": 75.41,
    "min": 40.8
   },
   "F-E": {
    "alpha": 22.07,
    "min": 30.2
   }
  }
 },
 "digit": {
  "metrics": {
   "cr_mean": 1.34,
   "route_ratio": 94.961,
   "lut": 22535,
   "spread": 131.4,
   "high_fanout": 9,
   "wns": -1.025
  },
  "actions": {
   "C-D": {
    "alpha": 21.38,
    "min": 23.2
   },
   "C-N": {
    "alpha": 48.48,
    "min": 52.4
   },
   "C-E": {
    "alpha": 38.21,
    "min": 22.6
   },
   "F-D": {
    "alpha": 54.44,
    "min": 20.2
   },
   "F-N": {
    "alpha": 53.9,
    "min": 41.6
   },
   "F-E": {
    "alpha": 35.28,
    "min": 15.9
   }
  }
 },
 "finn": {
  "metrics": {
   "cr_mean": 2.04,
   "route_ratio": 62.751,
   "lut": 73649,
   "spread": 255.1,
   "high_fanout": 4,
   "wns": -1.91
  },
  "actions": {
   "C-D": {
    "alpha": 33.17,
    "min": 55.6
   },
   "C-N": {
    "alpha": 30.56,
    "min": 65.2
   },
   "C-E": {
    "alpha": 49.77,
    "min": 46.2
   },
   "F-D": {
    "alpha": 64.26,
    "min": 40.8
   },
   "F-N": {
    "alpha": 55.58,
    "min": 44.2
   },
   "F-E": {
    "alpha": 66.72,
    "min": 35.1
   }
  }
 },
 "fir": {
  "metrics": {
   "cr_mean": 1.46,
   "route_ratio": 39.349,
   "lut": 603,
   "spread": 332.3,
   "high_fanout": 0,
   "wns": -0.313
  },
  "actions": {
   "C-D": {
    "alpha": 22.01,
    "min": 14.2,
    "note": "EWIDE 우회로 산물 — exp27 에서는 창 실패로 명시 실패함(비독립 표본)"
   },
   "C-N": {
    "alpha": 22.01,
    "min": 14.1,
    "note": "EWIDE 우회로 산물 — exp27 에서는 창 실패로 명시 실패함(비독립 표본)"
   },
   "C-E": {
    "alpha": 22.01,
    "min": 13.9,
    "note": "EWIDE 우회로 산물 — exp27 에서는 창 실패로 명시 실패함(비독립 표본)"
   },
   "F-D": {
    "alpha": 20.45,
    "min": 12.3
   },
   "F-N": {
    "alpha": 12.29,
    "min": 15.0
   },
   "F-E": {
    "alpha": 22.01,
    "min": 12.1
   }
  }
 },
 "logicnets": {
  "metrics": {
   "cr_mean": 1.04,
   "route_ratio": 82.104,
   "lut": 30839,
   "spread": 111.9,
   "high_fanout": 24,
   "wns": -0.978
  },
  "actions": {
   "C-D": {
    "alpha": 110.32,
    "min": 19.9
   },
   "C-N": {
    "alpha": 118.37,
    "min": 38.5
   },
   "C-E": {
    "alpha": 118.92,
    "min": 20.7
   },
   "F-D": {
    "alpha": 0.0,
    "min": 19.0
   },
   "F-N": {
    "alpha": 38.53,
    "min": 30.4
   },
   "F-E": {
    "alpha": 118.64,
    "min": 16.2
   }
  }
 },
 "optical": {
  "metrics": {
   "cr_mean": 0.38,
   "route_ratio": 51.897,
   "lut": 33803,
   "spread": 15.2,
   "high_fanout": 0,
   "wns": -1.078
  },
  "actions": {
   "C-D": {
    "alpha": 34.18,
    "min": 20.9
   },
   "C-N": {
    "alpha": 20.78,
    "min": 26.8
   },
   "C-E": {
    "alpha": 29.1,
    "min": 17.4
   },
   "F-D": {
    "alpha": 9.67,
    "min": 17.9
   },
   "F-N": {
    "alpha": 26.61,
    "min": 21.4
   },
   "F-E": {
    "alpha": 22.7,
    "min": 18.2
   }
  }
 },
 "spam": {
  "metrics": {
   "cr_mean": 0.02,
   "route_ratio": 53.198,
   "lut": 5361,
   "spread": 8.4,
   "high_fanout": 3,
   "wns": -0.686
  },
  "actions": {
   "C-D": {
    "alpha": 27.89,
    "min": 26.3
   },
   "C-N": {
    "alpha": 0.0,
    "min": 31.2
   },
   "C-E": {
    "alpha": 19.38,
    "min": 27.8
   },
   "F-D": {
    "alpha": 0.0,
    "min": 21.4
   },
   "F-N": {
    "alpha": 8.78,
    "min": 24.4
   },
   "F-E": {
    "alpha": 0.19,
    "min": 14.5
   }
  }
 },
 "vexriscv": {
  "metrics": {
   "cr_mean": 0.48,
   "route_ratio": 83.895,
   "lut": 1906,
   "spread": 53.5,
   "high_fanout": 0,
   "wns": -1.654
  },
  "actions": {
   "C-D": {
    "alpha": 140.28,
    "min": 12.3
   },
   "C-N": {
    "alpha": 157.77,
    "min": 15.0
   },
   "C-E": {
    "alpha": 154.08,
    "min": 11.3
   },
   "F-D": {
    "alpha": 137.05,
    "min": 11.7
   },
   "F-N": {
    "alpha": 156.24,
    "min": 13.7
   },
   "F-E": {
    "alpha": 140.28,
    "min": 10.7
   }
  }
 },
 "vexriscv_v2": {
  "metrics": {
   "cr_mean": 0.0,
   "route_ratio": 56.909,
   "lut": 2113,
   "spread": 11.5,
   "high_fanout": 0,
   "wns": -0.946
  },
  "actions": {
   "C-D": {
    "alpha": 32.1,
    "min": 12.2
   },
   "C-N": {
    "alpha": 0.0,
    "min": 17.5
   },
   "C-E": {
    "alpha": 13.56,
    "min": 10.0
   },
   "F-D": {
    "alpha": 9.05,
    "min": 11.6
   },
   "F-N": {
    "alpha": 4.96,
    "min": 16.7
   },
   "F-E": {
    "alpha": 0.0,
    "min": 9.4
   }
  }
 },
 "vtr_mcml": {
  "metrics": {
   "cr_mean": 2.1,
   "route_ratio": 61.128,
   "lut": 43311,
   "spread": 184.0,
   "high_fanout": 4,
   "wns": -14.527
  },
  "actions": {
   "C-D": {
    "alpha": 15.98,
    "min": 57.1
   },
   "C-N": {
    "alpha": 16.9,
    "min": 51.4
   },
   "C-E": {
    "alpha": 11.38,
    "min": 50.0
   },
   "F-D": {
    "alpha": 14.75,
    "min": 45.9
   },
   "F-N": {
    "alpha": 16.64,
    "min": 52.0
   },
   "F-E": {
    "alpha": 16.42,
    "min": 59.7
   }
  }
 },
 "vtr_v2": {
  "metrics": {
   "cr_mean": 2.0,
   "route_ratio": 49.491,
   "lut": 45700,
   "spread": 148.0,
   "high_fanout": 4,
   "wns": -12.885
  },
  "actions": {
   "C-D": {
    "alpha": 1.74,
    "min": 52.0
   },
   "C-N": {
    "alpha": 3.77,
    "min": 45.8
   },
   "C-E": {
    "alpha": 3.78,
    "min": 55.6
   },
   "F-D": {
    "alpha": 0.86,
    "min": 45.5
   },
   "F-N": {
    "alpha": 4.4,
    "min": 56.6
   },
   "F-E": {
    "alpha": 3.17,
    "min": 54.5
   }
  }
 }
}

# exp28: 일반 순위표 — 직전 승자 계열별 2수 기대 이득(실험3 전수 집계).
# 기대 이득 = mean(max(delta_true,0)), 동률은 이득 발생 횟수. 신호 규칙이 안 걸릴 때만 사용.
G2_RANK = {
 "F": [
  {
   "action": "F-E",
   "ev_mhz": 1.043,
   "n_pos": 1,
   "n": 5
  },
  {
   "action": "F-N",
   "ev_mhz": 0.398,
   "n_pos": 1,
   "n": 5
  },
  {
   "action": "C-D",
   "ev_mhz": 0.0,
   "n_pos": 0,
   "n": 5
  },
  {
   "action": "C-E",
   "ev_mhz": 0.0,
   "n_pos": 0,
   "n": 5
  },
  {
   "action": "C-N",
   "ev_mhz": 0.0,
   "n_pos": 0,
   "n": 5
  },
  {
   "action": "F-D",
   "ev_mhz": 0.0,
   "n_pos": 0,
   "n": 5
  }
 ],
 "C": [
  {
   "action": "F-N",
   "ev_mhz": 3.713,
   "n_pos": 3,
   "n": 8
  },
  {
   "action": "F-D",
   "ev_mhz": 3.581,
   "n_pos": 4,
   "n": 8
  },
  {
   "action": "C-D",
   "ev_mhz": 0.906,
   "n_pos": 3,
   "n": 8
  },
  {
   "action": "C-E",
   "ev_mhz": 0.166,
   "n_pos": 1,
   "n": 8
  },
  {
   "action": "F-E",
   "ev_mhz": 0.048,
   "n_pos": 1,
   "n": 8
  },
  {
   "action": "C-N",
   "ev_mhz": 0.0,
   "n_pos": 0,
   "n": 8
  }
 ]
}
