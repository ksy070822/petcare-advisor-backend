# 멀티 에이전트 시스템 개선 사항

## 📋 개선 요약

이번 개선 작업에서는 다음과 같은 주요 기능들이 추가/개선되었습니다:

1. **Medical Agent 프롬프트 고도화**
2. **PSHVM 레벨링 구조 도입**
3. **협진 시스템 (Collaborative Agent) 추가**
4. **약물 안내 기능 추가**
5. **FAQ 데이터 활용 서비스**
6. **추천 질문 기능**
7. **Report Builder 개선**

---

## 🔧 상세 개선 내용

### 1. Medical Agent 프롬프트 개선

**변경 사항:**
- 종별 특화 강화: 모든 진단이 해당 종에 특화되도록 프롬프트 개선
- Reasoning 구조화: 각 감별진단에 대해 `evidence_for`, `evidence_against`, `missing_info` 필드 추가
- 약물 안내 통합: Medical Agent가 약물 종류에 대한 간단한 안내 제공

**새로운 출력 형식:**
```json
{
    "primary_assessment": "가장 가능성이 높은 진단",
    "riskLevel": "low|medium|high|Emergency",
    "possible_diseases": [
        {"name": "질병명", "probability": 0.0-1.0}
    ],
    "reasoning": [
        {
            "diagnosis": "감별진단 대상 질병명",
            "confidence": 0.75,
            "evidence_for": ["지지하는 증거들"],
            "evidence_against": ["반하는 증거들"],
            "missing_info": ["필요한 추가 정보"]
        }
    ],
    "medication_guidance": "약물 안내",
    "final_notes_for_care_agent": "Care Agent 전달 지시사항"
}
```

**파일:** `src/petcare_advisor/agents/medical_agent.py`

---

### 2. PSHVM (Pet Safety and Health Vulnerability Matrix) 레벨링 구조

**변경 사항:**
- Triage Agent에 PSHVM 가중치 시스템 도입
- ACT System (Red/Orange/Yellow/Green) 색상 레벨 적용
- 증상 지속 시간, 나이, 품종별 취약성에 따른 가중치 계산

**가중치 규칙:**
- 증상 지속 7일 이상: +2점
- 증상 지속 48시간 이상: +1점
- 노령견 (7세 이상): +1점
- 품종 취약성 (불독, 퍼그, 골든 리트리버, 래브라도 등): +1점

**ACT 색상 레벨:**
- **Red (즉각 조치)**: 호흡곤란, 의식불명, 심한 출혈, 경련, 마비, 쇼크 → 5점
- **Orange (수시간 내)**: 지속적인 구토/설사, 48시간 이상 식욕 부진 → 3-4점
- **Yellow (24시간 내)**: 기침/재채기, 경미한 피부 문제 → 1-2점
- **Green**: 일반 정보 요청 → 0점

**새로운 출력 필드:**
```json
{
    "urgency_score": 3,  // 최종 점수 (가중치 반영)
    "base_score": 2,      // 가중치 적용 전 초기 점수
    "weight_adjustment": 1,  // 적용된 가중치
    "act_color": "Orange",   // ACT 색상 레벨
    "pshvm_factors": ["증상 지속 48시간 이상 (+1점)", "노령견 (8세, +1점)"]
}
```

**파일:** `src/petcare_advisor/agents/triage_agent.py`

---

### 3. 협진 시스템 (Collaborative Agent)

**새로운 에이전트 추가:**
- Medical Agent와 Triage Agent의 결과를 교차 검증
- 불일치 감지 및 해결
- Claude Sonnet 4 또는 GPT-4o를 사용한 수석 수의사 검토

**기능:**
1. **불일치 검출**: Medical Agent와 Triage Agent의 위험도 평가 비교
2. **교차 검증**: Claude/GPT-4o를 사용한 독립적 검토
3. **합의 도출**: 안전 우선 원칙에 따라 최종 위험도 결정

**출력 형식:**
```json
{
    "discrepancy_analysis": {
        "has_discrepancies": true/false,
        "discrepancy_type": "medical_higher|triage_higher|moderate_mismatch",
        "needs_review": true/false
    },
    "review_result": {
        "agreement_with_medical": true/false,
        "recommended_risk_level": "low|medium|high|Emergency",
        "recommended_triage_score": 0-5,
        "confidence_level": "높음|중간|낮음"
    },
    "consensus": {
        "consensus_reached": true/false,
        "final_risk_level": "low|medium|high|Emergency",
        "final_triage_score": 0-5,
        "confidence_score": 0.0-1.0
    }
}
```

**파일:** `src/petcare_advisor/agents/collaborative_agent.py`

---

### 4. 약물 안내 기능

**새로운 서비스 추가:**
- `medication_service.py`: medicationLogs 데이터를 활용한 약물 안내
- 증상 및 진단에 따른 약물 종류 추천
- Careplan Agent에 통합

**기능:**
- 증상 키워드 기반 약물 매칭
- 효과성 평가 기반 추천
- 일반적인 약물 안내 메시지 생성

**출력 예시:**
```json
{
    "has_medication_guidance": true,
    "medication_types": [
        {
            "name": "항생제",
            "typical_usage": "1일 1회 식전 30분",
            "effectiveness": 5
        }
    ],
    "recommended_type": "항생제",
    "general_guidance": "항생제 종류의 약으로 호전될 수 있어요..."
}
```

**파일:** `src/petcare_advisor/tools/medication_service.py`

---

### 5. FAQ 데이터 활용 서비스

**새로운 서비스 추가:**
- `faq_service.py`: owner_faq 데이터를 활용한 FAQ 검색
- 증상 및 종별 관련 FAQ 제공
- 추천 질문 생성 기능

**기능:**
1. **관련 FAQ 검색**: 증상 키워드 기반 FAQ 매칭
2. **추천 질문 생성**: 증상별 맞춤형 후속 질문 3개 생성

**추천 질문 예시:**
```json
[
    {"id": "vomiting_frequency", "question": "구토는 하루에 몇 회 정도 발생하나요?"},
    {"id": "vomiting_content", "question": "구토물에 혈액이나 이상한 색이 섞여 있나요?"},
    {"id": "vomiting_timing", "question": "구토는 식사 전후 언제 주로 발생하나요?"}
]
```

**파일:** `src/petcare_advisor/tools/faq_service.py`

---

### 6. Root Orchestrator 업데이트

**변경 사항:**
- 협진 시스템 단계 추가 (Step 5)
- 추천 질문 생성 통합
- 파이프라인 순서 업데이트

**새로운 파이프라인:**
1. Symptom Intake Agent
2. Vision Agent (optional)
3. Medical Agent
4. Triage Agent
5. **Collaborative Agent** (NEW)
6. Careplan Agent
7. Final Report Builder

**파일:** `src/petcare_advisor/agents/root_orchestrator.py`

---

### 7. Report Builder 개선

**변경 사항:**
- 협진 결과 포함
- 약물 안내 정보 추가
- 추천 질문 포함
- PSHVM 정보 포함

**새로운 리포트 구조:**
```json
{
    "triage": {
        "urgency_score": 3,
        "base_score": 2,
        "weight_adjustment": 1,
        "act_color": "Orange",
        "pshvm_factors": ["증상 지속 48시간 이상 (+1점)"]
    },
    "care_plan": {
        "medication_guidance": "항생제 종류의 약으로 호전될 수 있어요...",
        "medication_types": [...]
    },
    "collaborative_diagnosis": {
        "discrepancy_analysis": {...},
        "consensus": {...}
    },
    "recommended_questions": [
        {"id": "...", "question": "..."}
    ]
}
```

**파일:** `src/petcare_advisor/tools/report_builder.py`

---

## 📊 데이터 구조 변경

### GraphState 업데이트
- `collaborative_data` 필드 추가

### TriageRequest 업데이트
- 기존 필드 유지 (추가 변경 없음)

---

## 🔄 통합 흐름

```
1. 사용자 증상 입력
   ↓
2. Symptom Intake Agent → 구조화된 증상 데이터
   ↓
3. Vision Agent (이미지 있을 경우) → 시각적 분석
   ↓
4. Medical Agent → 감별진단 + 약물 안내
   ↓
5. Triage Agent → PSHVM 기반 응급도 판정
   ↓
6. Collaborative Agent → 교차 검증 및 합의
   ↓
7. Careplan Agent → 홈케어 가이드 + 약물 안내 통합
   ↓
8. Report Builder → 최종 리포트 (추천 질문 포함)
```

---

## 🚀 향후 개선 사항

1. **Firebase 통합**: medicationLogs와 FAQ 데이터를 Firebase에서 직접 조회
2. **이미지 분석 강화**: Vision Agent 프롬프트 고도화
3. **스트리밍 응답**: 실시간 응답 스트리밍 지원
4. **추천 질문 인터랙티브**: 사용자 선택에 따른 추가 답변 제공
5. **진료기록서 생성**: 보호자용/병원용 분리된 진료기록서 생성

---

## 📝 참고 사항

- **비용 최적화**: Medical Agent는 GPT-4o-mini 사용 (Claude 대신)
- **협진 시스템**: Claude Sonnet 4가 없으면 GPT-4o 사용
- **하위 호환성**: 기존 API 응답 형식 유지 (추가 필드만 확장)

---

## ✅ 테스트 체크리스트

- [ ] Medical Agent가 새로운 형식으로 출력하는지 확인
- [ ] PSHVM 가중치가 올바르게 계산되는지 확인
- [ ] Collaborative Agent가 불일치를 감지하는지 확인
- [ ] 약물 안내가 Careplan에 포함되는지 확인
- [ ] 추천 질문이 리포트에 포함되는지 확인
- [ ] 전체 파이프라인이 정상 작동하는지 확인

---

## 📚 관련 파일 목록

### 수정된 파일
- `src/petcare_advisor/agents/medical_agent.py`
- `src/petcare_advisor/agents/triage_agent.py`
- `src/petcare_advisor/agents/careplan_agent.py`
- `src/petcare_advisor/agents/root_orchestrator.py`
- `src/petcare_advisor/tools/report_builder.py`
- `src/petcare_advisor/shared/types.py`
- `src/petcare_advisor/main.py`
- `src/petcare_advisor/agents/__init__.py`

### 새로 생성된 파일
- `src/petcare_advisor/agents/collaborative_agent.py`
- `src/petcare_advisor/tools/medication_service.py`
- `src/petcare_advisor/tools/faq_service.py`

---

**작성일:** 2025-01-02
**버전:** v0.2.0

