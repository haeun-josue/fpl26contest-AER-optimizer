# -*- coding: utf-8 -*-
"""exp27 규칙 엔진 — 프레임워크 팔의 결정적 판단 (데이터 모듈: `_` 접두 — MCP 미등록).

전 규칙의 근거는 exp26 research/(rule_evidence.csv) — 규칙 ID 를 주석에 병기.
설계 원칙: 판단은 전부 순수 함수(상태 dict 입력 → 결정 출력) — 오프라인 전수 시험 가능.
행동 어휘: C-D C-N C-E F-D F-N F-E + route_directive (전역 6종+rd — 사용자 확정 8/7).
"""

ACTIONS = ['C-D', 'C-N', 'C-E', 'F-D', 'F-N', 'F-E']

# ── 시간 모형 (목적: 완주 불가 전략 차단 — 비보수. 상수는 이 모듈 단일 위치 — 항목7) ──
TIME_SAFETY = 1.15          # 상한 계수 — budget_ok 한 곳에서만 적용(항목7)
RESERVE_S = 180             # 저장·마무리 예약분
G2_RATIO = {'D': 1.3, 'E': 1.3, 'N': 1.5}    # est = base × 계수 + 300 (승인 8/9 항목7 —
                                             # 실험값, 실측 후 재보정 등록. 구값 E1.35/N2.2)
G2_N_FLOOR_S = 1500         # netdelay 바닥 비용 — amd 실측(311s 설계에서 1379~1461s): 배율이 아니라 바닥
RD_EST = (0.75, 600)        # est(RD) = max(600, 0.75×dur1) — 실측 12/13 설계 비율 ≤0.5 을 여유 있게 덮고,
                            # finn 형(비율 1.5)은 통상 예산 문맥에서 차단됨(S3 소급: 1530s 잔여 vs est 1862s).
                            # 잔여 위험: 예산이 넉넉한 문맥의 finn 형은 여전히 과소추정 — γ-한정 손실, S5 캘리브레이션.

# ── base 폴백 사슬 (항목7·8 승인 8/9) ────────────────────────────────────────
G3_STATIC_MIN = {'C-D': 27.9, 'C-E': 26.6, 'C-N': 34.8,   # 13종 평균(분) — 항목7 폴백
                 'F-D': 23.8, 'F-E': 23.5, 'F-N': 30.8}   # 3순위 전용 (항목8: est 용도만)
BASE_FLOOR_S = 60           # base 하한 클램프 (항목7 — 빈값·0·무한대 불가)
BASE_LAST_RESORT_S = 900    # 최후 폴백. frag 의 TCL open timeout 900 과 다른 용도 — 이름 분리(항목7)

def base_for_action(action, measured):
    """base(초) 결정 — 항목7 순서: 같은 계열의 완주 실측(max) → 아무 팔의 완주 실측(max)
    → 정적 상수표 → 최후 900s. 어느 경로로든 항상 유한 양수(하한 60s).
    measured: {행동: 완주 벽시계 초} — 실패(X)한 실행의 시간은 호출측이 넣지 않는다."""
    fam = [v for a, v in measured.items() if a and a[0] == action[0] and v and v > 0]
    if fam:
        base = max(fam)
    else:
        anyv = [v for v in measured.values() if v and v > 0]
        if anyv:
            base = max(anyv)
        elif action in G3_STATIC_MIN:
            base = G3_STATIC_MIN[action] * 60.0
        else:
            base = BASE_LAST_RESORT_S
    return max(BASE_FLOOR_S, float(base))

def est_g2_s(dur1_s, action):
    est = dur1_s * G2_RATIO[action[-1]] + 300
    if action.endswith('N'):
        est = max(est, G2_N_FLOOR_S)
    return est

def est_rd_s(dur1_s):
    return max(RD_EST[1], dur1_s * RD_EST[0])

def budget_ok(left_s, est_s):
    """예산 게이트(하드): 완주+저장 가능해야 실행."""
    return left_s >= est_s * TIME_SAFETY + RESERVE_S

def value_ok(gain_est_mhz, alpha_now, est_s):
    """가치 게이트: 한계 부등식 Δα > 0.1·α·Δt(h) [T01, CONFIRMED]."""
    return gain_est_mhz > 0.1 * alpha_now * (est_s / 3600.0)

# ── 1수 후보 (G1 — 시작 상태 전용. U01·U03·U04) ─────────────────────────────
CR_LO, CR_HI = 1.2, 1.4     # U01 문턱 1.3 의 경계 완충 — 구간 내는 계열 교차쌍으로 2팔이 흡수

def g1_candidates(diag):
    """diag: {'cr_mean','route_ratio','lut',...} → top-2 행동 [1순위, 2순위] + 근거.

    U01(CONFIRMED): cr<1.3→C, ≥1.3→F. 경계(1.2~1.4)는 교차쌍 [C측 1순위, F측 1순위].
    U03(SUPPORTED): C 계열 — rr≥77.6→C-N, 아니면 C-D (C-E 는 2순위 후보).
    U04(SUPPORTED): F 계열 — 바닥 보증 F-N 1순위, 후회 최소 F-E 2순위.
    """
    cr = diag.get('cr_mean')
    rr = diag.get('route_ratio')
    def c_rank():
        if rr is not None and rr >= 77.6:
            return ['C-N', 'C-D']
        return ['C-D', 'C-E']
    f_rank = ['F-N', 'F-E']
    if cr is None:
        return [c_rank()[0], f_rank[0]], 'cr 측정 실패 — 교차쌍(저후회)'
    if cr < CR_LO:
        return c_rank(), f'U01: cr {cr}<{CR_LO} → C 계열'
    if cr > CR_HI:
        return f_rank, f'U01: cr {cr}>{CR_HI} → F 계열'
    return [c_rank()[0], f_rank[0]], f'U01 경계(cr {cr}) → 교차쌍 — 2팔이 흡수'

# ── 1수 이후: 종료/2수 판단 (T01·T02·T05·T06·U09·U10) ───────────────────────
G2_GAIN_EST = {              # 미지 설계용 기대 이득(실측 최소~중앙 — 낙관 금지)
    'small_c_winner': 2.9,   # U09: 소형 C-승자 → F 전환, 실측 +0.17~+20.1 의 하위값
    'cr0_c_winner': 2.8,     # T06: cr_max=0 C-승자, 실측 +0.4~+22.0 의 하위값(amd)
}

def g2_decision(state, history, left_s):
    """state: G1 승자 상태 지표 {'lut','cr_max','overlap_max_share',...}
    history: {'g1_action','g1_alpha','g1_dur_s','zero_actions':set(관측 무득 행동)}
    → {'go': bool, 'candidates': [...], 'why': str}
    """
    lut = state.get('lut') or 0
    fam1 = history['g1_action'][0]
    a1 = history['g1_alpha']; d1 = history['g1_dur_s']
    # 종료 신호 (utility 근거)
    if state.get('overlap_max_share') == 1.0:
        return {'go': False, 'candidates': [], 'why': 'T02: 병목 고착(share=1.0) → 생략'}
    if fam1 == 'C' and lut >= 30700:
        return {'go': False, 'candidates': [], 'why': 'T05: 대형 C-승자 → 생략'}
    # 진입 신호 + 후보
    cands, gain_key = [], None
    if fam1 == 'C' and lut <= 5500:
        cands, gain_key = ['F-N', 'F-D'], 'small_c_winner'   # U09 (+vexriscv_v2 F-N +6.65 근거로 N 우선)
    elif fam1 == 'C' and state.get('cr_max') == 0:
        cands, gain_key = ['F-D', 'F-N'], 'cr0_c_winner'     # T06 + 교차 우세(U01 다발)
    else:
        return {'go': False, 'candidates': [],
                'why': '진입 신호 없음(F-승자 또는 무신호 중형) — 기본 생략(U08: G2 기본값은 악화)'}
    cands = [c for c in cands if c not in history.get('zero_actions', set())]   # U10
    if not cands:
        return {'go': False, 'candidates': [], 'why': 'U10: 후보 전원 관측 무득 이력'}
    est = est_g2_s(d1, cands[0])
    if not budget_ok(left_s, est):
        return {'go': False, 'candidates': cands, 'why': f'예산 게이트: left {left_s:.0f}s < est {est:.0f}s×{TIME_SAFETY}+{RESERVE_S}'}
    if not value_ok(G2_GAIN_EST[gain_key], a1, est):
        return {'go': False, 'candidates': cands, 'why': 'T01 가치 게이트 미달'}
    return {'go': True, 'candidates': cands, 'why': f'{gain_key} 신호 + 게이트 통과'}

# ── RD 판단 (R01·R02·R03·R04·R05·R06 — 순서형 조합 R07) ─────────────────────
def rd_decision(state, history, left_s):
    """state: 현재 상태 지표, history: {'g1_hf'(G1 승자 상태 hf), 'last_family'(직전 채택 계열),
    'alpha_now','g1_dur_s','rd_done_states':set}  → {'go','why'}"""
    if history.get('state_key') in history.get('rd_done_states', set()):
        return {'go': False, 'why': 'R06: 같은 상태 RD 재시도 금지(결정론)'}
    # R04 적용 범위: "G2 에서 C 계열이 채택된 직후"만. G1 C-승자 뒤의 rd 는 실측 이득
    # 4설계 중 2(logicnets·spam)가 C-승자라 차단하면 안 된다(S3 소급 시험에서 발견·수정).
    if history.get('last_g2_family') == 'C':
        return {'go': False, 'why': 'R04: G2 C-계열 채택 직후 — 생략(0/4, 표본 소)'}
    rr = state.get('route_ratio')
    if rr is not None and rr < 40:
        return {'go': False, 'why': 'R03: route%<40(logic 지배) — 무득 0/7'}
    if history.get('g1_hf') == 0:
        return {'go': False, 'why': 'R01: hf=0 설계 — 전 사슬 무득(13상태 반례 0)'}
    sm = state.get('spread_max')
    if sm is not None and sm < 30:
        return {'go': False, 'why': 'R02: spread_max<30 — 필요조건 미달'}
    est = est_rd_s(history['g1_dur_s'])
    if not budget_ok(left_s, est):
        return {'go': False, 'why': f'예산 게이트: left {left_s:.0f}s < est {est:.0f}s'}
    # R05: BE 는 "예상 이득" 추정이 없으므로 실행 후 채택 판정으로 넘김(실행 자체가 1회 실측 — R07 절차 5)
    return {'go': True, 'why': '게이트 전 통과 → 1회 실측(결정론 — R06)'}
