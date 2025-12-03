"""Triage Agent - Computes urgency level and triage classification using OpenAI GPT-4o-mini."""

import json
import logging
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from ..config import get_settings
from ..shared.constants import OUTPUT_KEY_TRIAGE, TRIAGE_INFO, TRIAGE_LOW, TRIAGE_MODERATE, TRIAGE_HIGH, TRIAGE_EMERGENCY

logger = logging.getLogger(__name__)
settings = get_settings()


class TriageAgentInput(BaseModel):
    """Input schema for triage agent tool."""
    symptom_data: Dict[str, Any] = Field(..., description="Structured symptom data")
    medical_data: Dict[str, Any] = Field(..., description="Medical analysis data")


def _triage_agent_function(
    symptom_data: Dict[str, Any],
    medical_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Compute urgency score and triage level based on symptoms and medical analysis.
    
    This agent computes:
    - Urgency score (0-5)
    - Triage level (INFO, LOW, MODERATE, HIGH, EMERGENCY)
    - Justification for the triage level
    
    Args:
        symptom_data: Structured symptom data
        medical_data: Medical analysis data
        
    Returns:
        Dictionary with output_key "triage_result" containing triage assessment
    """
    logger.info("[TRIAGE] Computing triage level")
    
    # Initialize OpenAI GPT-4o-mini model
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.openai_api_key,
        temperature=0.2,
    )
    
    # Extract relevant data
    symptom_structured = symptom_data.get("structured_data", {})
    medical_structured = medical_data.get("structured_data", {})
    
    # 종 정보 추출
    species = symptom_structured.get('species', '알 수 없음')
    
    # Build context (한글)
    context_parts = []
    context_parts.append(f"종: {species}")
    context_parts.append(f"주요 증상: {', '.join(symptom_structured.get('main_symptoms', []))}")
    context_parts.append(f"위험 신호: {', '.join(symptom_structured.get('red_flags', []))}")
    context_parts.append(f"심각도: {symptom_structured.get('severity_perception', '알 수 없음')}")
    context_parts.append(f"지속 기간: {symptom_structured.get('duration', '알 수 없음')}")
    
    top_diagnosis = medical_structured.get("differential_diagnosis", [])
    if top_diagnosis:
        context_parts.append(f"주요 감별진단: {top_diagnosis[0].get('condition', '알 수 없음')}")
    
    context = "\n".join(context_parts)
    
    # PSHVM (Pet Safety and Health Vulnerability Matrix) 가중치 계산
    symptom_structured = symptom_data.get("structured_data", {})
    age = symptom_structured.get('age', 0)
    breed = symptom_structured.get('breed', '')
    duration = symptom_structured.get('duration', '')
    
    # 가중치 계산
    weight_adjustment = 0
    weight_reasons = []
    
    # 증상 지속 시간 가중치
    if "7일" in str(duration) or "일주일" in str(duration):
        weight_adjustment += 2
        weight_reasons.append("증상 지속 7일 이상 (+2점)")
    elif "48시간" in str(duration) or "2일" in str(duration):
        weight_adjustment += 1
        weight_reasons.append("증상 지속 48시간 이상 (+1점)")
    
    # 노령견 가중치
    if age and age >= 7:
        weight_adjustment += 1
        weight_reasons.append(f"노령견 ({age}세, +1점)")
    
    # 품종별 취약성 가중치 (예: 불독의 호흡기, 대형견의 고관절)
    breed_vulnerabilities = {
        "불독": "호흡기 취약",
        "퍼그": "호흡기 취약",
        "골든 리트리버": "고관절 취약",
        "래브라도": "고관절 취약",
    }
    if breed and any(v in breed for v in breed_vulnerabilities.keys()):
        weight_adjustment += 1
        weight_reasons.append(f"품종 취약성 ({breed}, +1점)")
    
    # System prompt for triage (병원 컨셉 - 응급실 트리아지 담당)
    system_prompt_base = f"""당신은 동물병원의 [응급실 트리아지 담당자]입니다. 주치의 선생님의 진단 결과를 바탕으로 현재 상황이 얼마나 급한지 분류하는 것이 당신의 역할입니다.

**중요**: 현재 환자는 **{species}**입니다. 응급도 판단은 반드시 {species}에 특화된 기준을 사용해야 합니다. 다른 종의 기준을 적용하지 마세요.

## PSHVM (Pet Safety and Health Vulnerability Matrix) 레벨링 시스템

### 색상 레벨 (ACT System):
- **Red (즉각 조치)**: 호흡곤란, 의식불명, 심한 출혈, 경련, 마비, 쇼크 → 무조건 5점 판정 후 병원 이송 권고
- **Orange (수시간 내)**: 지속적인 구토/설사, 48시간 이상 식욕 부진, 심한 통증 → 3-4점
- **Yellow (24시간 내)**: 기침/재채기, 경미한 피부 문제 → 1-2점

### 가중치 규칙 (이미 계산된 가중치: +{weight_adjustment}점):
{chr(10).join([f"- {reason}" for reason in weight_reasons]) if weight_reasons else "- 가중치 없음"}

**주의**: 위 가중치는 초기 점수에 더해집니다. 최종 점수는 0-5 범위를 초과하지 않도록 조정하세요.

말투 지침:
- 빠르고 간단하며 직접적이어야 합니다
- 위급도를 명확하게 판단하고, 그 근거를 간결하게 설명합니다
- 보호자가 당황하지 않도록 차분하지만, 긴급한 상황은 확실히 전달합니다

응급도 레벨:
- INFO: 일반 정보 요청, 즉각적인 우려 없음
- LOW: 경미한 문제, 24-48시간 기다려도 됨
- MODERATE: 24시간 내 수의사 방문 권장
- HIGH: 6-12시간 내 수의사 방문 권장
- EMERGENCY: 즉시 수의학적 치료 필요

응급도 점수 (0-5):
- 0: INFO
- 1: LOW
- 2: MODERATE
- 3: HIGH
- 4: EMERGENCY
- 5: 중대 응급 (Red 레벨)

고려사항:
- 위험 신호 지표 (출혈, 경련, 실신, 호흡곤란, 의식불명, 심한 통증)
- 증상 심각도 및 지속 기간
- 위험 요인 (나이, 품종, 기저질환)
- 감별진단 가능성
- PSHVM 가중치 규칙

모든 텍스트는 반드시 한글로 작성하세요.

다음 형식의 유효한 JSON만 반환하세요:"""
    
    json_example = """
{
    "urgency_score": 숫자 (0-5, 가중치 반영),
    "base_score": 숫자 (가중치 적용 전 초기 점수),
    "weight_adjustment": 숫자 (적용된 가중치),
    "triage_level": "INFO|LOW|MODERATE|HIGH|EMERGENCY",
    "act_color": "Red|Orange|Yellow|Green",
    "justification": "상세한 설명 (한글로 작성)",
    "risk_assessment": "위험 평가 설명 (한글로 작성)",
    "pshvm_factors": ["적용된 PSHVM 요인들"],
    "time_sensitivity": 숫자 (수의사 방문 권장 시간, INFO의 경우 null)
}"""
    
    system_prompt = system_prompt_base + json_example
    
    try:
        # Call LLM
        prompt = f"{system_prompt}\n\n케이스 정보:\n{context}"
        response = llm.invoke(prompt)
        content = response.content
        
        # Parse JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        structured_data = json.loads(content)
        
        # Validate triage level
        valid_levels = [TRIAGE_INFO, TRIAGE_LOW, TRIAGE_MODERATE, TRIAGE_HIGH, TRIAGE_EMERGENCY]
        if structured_data.get("triage_level") not in valid_levels:
            structured_data["triage_level"] = TRIAGE_INFO
        
        # PSHVM 가중치 적용 (이미 프롬프트에 포함되었지만, 안전장치로 다시 계산)
        base_score = structured_data.get("base_score", structured_data.get("urgency_score", 0))
        final_score = min(5, max(0, base_score + weight_adjustment))
        structured_data["urgency_score"] = final_score
        structured_data["base_score"] = base_score
        structured_data["weight_adjustment"] = weight_adjustment
        structured_data["pshvm_factors"] = weight_reasons
        
        # ACT Color 결정
        if final_score >= 4 or any(flag in symptom_structured.get("red_flags", []) for flag in ["bleeding", "seizure", "collapse", "difficulty_breathing", "unconscious"]):
            structured_data["act_color"] = "Red"
        elif final_score >= 3:
            structured_data["act_color"] = "Orange"
        elif final_score >= 1:
            structured_data["act_color"] = "Yellow"
        else:
            structured_data["act_color"] = "Green"
        
        logger.info(f"[TRIAGE] Triage level determined: {structured_data.get('triage_level')} (score: {final_score}, base: {base_score}, weight: +{weight_adjustment})")
        
        result = {
            "output_key": OUTPUT_KEY_TRIAGE,
            "structured_data": structured_data,
        }
        
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"[TRIAGE] JSON parsing error: {e}")
        return {
            "output_key": OUTPUT_KEY_TRIAGE,
            "structured_data": {
                "urgency_score": 0,
                "base_score": 0,
                "weight_adjustment": 0,
                "triage_level": TRIAGE_INFO,
                "act_color": "Green",
                "justification": "",
                "risk_assessment": "",
                "pshvm_factors": [],
                "time_sensitivity": None,
            }
        }
    except Exception as e:
        logger.error(f"[TRIAGE] Error: {e}")
        raise


# Create LangChain tool
triage_agent_tool = StructuredTool.from_function(
    func=_triage_agent_function,
    name="triage_agent",
    description="Compute urgency score and triage level. Use this after medical analysis.",
    args_schema=TriageAgentInput,
)
