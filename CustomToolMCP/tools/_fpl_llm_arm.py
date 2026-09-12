# -*- coding: utf-8 -*-
"""exp27 LLM 팔 — 1수 판단 프롬프트 생성·응답 검증 (데이터 모듈: `_` 접두, MCP 미등록).

입력 6종(설계서 §6): ①카탈로그(전결과) ②판단축 우선순위표 ③축별 최근접 이웃(사전 계산)
④반례·유보 ⑤저후회 fallback ⑥출력 JSON 스키마(근거 인용 강제).
LLM 실패·스키마 위반 시 호출측이 프레임워크 팔로 fallback 한다.
"""
import json
import _fpl_knowledge as K

AXIS_TABLE = """## 판단축별 판별 지표 (연구 실측 — 이 축의 일치만 유효, 다른 지표 유사성은 무정보)
1. 계열(C=창 압축 vs F=전역 재배치): cr_crossings_mean 만 본다. <1.3 → C, >=1.3 → F
   (12설계 유의 반례 0, CONFIRMED). 주의: spread·LUT 크기는 계열 판별에 무정보
   (실측: 크기·spread 유사한 corescore/finn 이 정반대 정답). 오판 비용 비대칭:
   F 쪽 실수 최대 -2.5MHz, C 쪽 실수 최대 -17MHz → 애매하면 F.
2. C 계열 지시자: route_ratio >= 77.6 → C-N(netdelay), <= 62.8 → C-N 금지(C-D 우선).
   62.8~77.6 은 무표본(유보 → C-D). (SUPPORTED)
3. F 계열 지시자: 판별 지표 없음(연구 결론 — 설계별 정답 갈림, 표본 5 미결).
   **기본값은 F-N(바닥 보증 — 13설계 붕괴 0, 최저 +4.4)**. F-E 는 cr·rr 축 최근접 이웃
   다수의 실측 승자가 F-E 일 때만 선택하라(이웃 승자가 갈리면 F-N 유지).
   F-D 는 이웃 중 F-D 승자(digit 형)와 매우 근접할 때만.
4. 근포화 예외: 6행동 산포 <5MHz 인 설계(amd 형)는 지시자 선택이 무의미 — 사전 지표 없음."""

CAVEATS = """## 반례·유보 (틀리기 쉬운 곳)
- cr 1.2~1.4 경계는 판정 유보 구간(무표본) — 이 구간이면 confidence=low 로 표시하라.
- netdelay(-N)는 시간 +5~12분 무조건(U05) — 이득 +2MHz 미만 예상이면 점수 손해.
- 카탈로그 fir 의 C 계열 값은 구식 우회로 산물 — fir 류(창 실패)에서 C 는 실패한다.
- 지표가 카탈로그 관측 범위 밖이면 유추 금지 — 저후회 기본값(계열 F, 지시자 N)을 쓰고 confidence=low."""

SCHEMA_TEXT = """## 출력 (JSON 한 줄만 — 다른 텍스트 금지)
{"action": "C-D|C-N|C-E|F-D|F-N|F-E", "basis": "<어느 축·어느 이웃·어느 규칙을 근거로 했는지 1~2문장>", "confidence": "high|med|low"}"""


def _neighbors(diag, catalog, axis, k=3):
    vals = []
    for d, c in catalog.items():
        v = c['metrics'].get(axis)
        if v is not None and diag.get(axis) is not None:
            vals.append((abs(v - diag[axis]), d, v))
    vals.sort()
    return vals[:k]


def build_g1_prompt(diag, exclude_design=None, variant_of=None):
    """diag: {'cr_mean','route_ratio','lut','spread','high_fanout','wns'} → (system, user) 문자열.
    exclude_design: leave-one-out 시험용(운영 미사용). variant_of: 지문 ②(수량 일치·조건 상이)
    일 때 일치한 설계명 — LLM 에게 '그 설계의 변형일 가능성' 단서를 준다(사용자 설계 8/7)."""
    catalog = {d: c for d, c in K.G1_CATALOG.items() if d != exclude_design}
    cat_lines = []
    for d, c in sorted(catalog.items()):
        m = c['metrics']
        acts = ' '.join(f"{a}:{v['alpha']}" for a, v in sorted(c['actions'].items()))
        cat_lines.append(f"{d}: cr={m['cr_mean']} rr={m['route_ratio']} lut={m['lut']} "
                         f"spread={m['spread']} hf={m['high_fanout']} | α: {acts}")
    nb = []
    for axis in ['cr_mean', 'route_ratio']:
        ns = _neighbors(diag, catalog, axis)
        nb.append(f"{axis} 축 최근접: " + ", ".join(f"{d}({v})" for _, d, v in ns))
    system = ("당신은 FPGA 배치·배선 최적화의 첫 수(전역 행동 1개)를 고르는 판단기다. "
              "실측 카탈로그와 판별 지식만 근거로 삼고, 근거 없는 직감을 쓰지 마라. "
              "출력은 JSON 한 줄뿐이다.")
    parts = [
        "## 신규 설계 진단",
        json.dumps(diag, ensure_ascii=False)]
    if variant_of and variant_of in catalog:
        parts.append(
            f"## 변형 단서 (지문 수량 일치·조건 상이)\n"
            f"이 설계는 자원 수량이 카탈로그의 {variant_of} 와 정확히 일치한다(클럭 주기 또는 시작 "
            f"타이밍만 다름). 같은 회로의 제약 변형일 가능성이 높다 — {variant_of} 행의 실측 α 를 "
            f"가장 가까운 근거로 쓰되, 판단축 지표(cr·rr)가 그 행과 다르면 지표 쪽을 따르라.")
    user = "\n\n".join(parts + [
        AXIS_TABLE,
        "## 축별 최근접 이웃 (프레임워크 사전 계산 — 이 축들만 유사도로 쓰라)",
        "\n".join(nb),
        "## 카탈로그 (13설계 × 6행동 실측 α)",
        "\n".join(cat_lines),
        CAVEATS,
        SCHEMA_TEXT])
    return system, user


def validate_llm_choice(text):
    """응답 → {'action','basis','confidence'} 또는 None(스키마 위반 — fallback 신호)."""
    try:
        s = text.strip()
        i, j = s.find('{'), s.rfind('}')
        if i < 0 or j < 0:
            return None
        obj = json.loads(s[i:j + 1])
        if obj.get('action') not in ('C-D', 'C-N', 'C-E', 'F-D', 'F-N', 'F-E'):
            return None
        if not obj.get('basis'):
            return None
        return obj
    except Exception:
        return None
