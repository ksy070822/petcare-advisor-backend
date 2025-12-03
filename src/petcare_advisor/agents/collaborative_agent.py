"""Collaborative Agent - Cross-validates medical and triage results for consensus."""

import json
import logging
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field
from ..config import get_settings
from ..shared.constants import OUTPUT_KEY_MEDICAL_ANALYSIS, OUTPUT_KEY_TRIAGE

logger = logging.getLogger(__name__)
settings = get_settings()


class CollaborativeAgentInput(BaseModel):
    """Input schema for collaborative agent tool."""
    symptom_data: Dict[str, Any] = Field(..., description="Structured symptom data")
    medical_data: Dict[str, Any] = Field(..., description="Medical analysis data")
    triage_data: Dict[str, Any] = Field(..., description="Triage assessment data")


def detect_discrepancies(
    medical_data: Dict[str, Any],
    triage_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Detect discrepancies between medical and triage assessments.
    
    Args:
        medical_data: Medical analysis result
        triage_data: Triage assessment result
        
    Returns:
        Dictionary with discrepancy analysis
    """
    medical_structured = medical_data.get("structured_data", {})
    triage_structured = triage_data.get("structured_data", {})
    
    medical_risk = medical_structured.get("riskLevel", "medium")
    triage_level = triage_structured.get("triage_level", "MODERATE")
    triage_score = triage_structured.get("urgency_score", 2)
    
    # Risk level mapping
    risk_mapping = {
        "low": "LOW",
        "medium": "MODERATE",
        "high": "HIGH",
        "Emergency": "EMERGENCY",
    }
    medical_triage_equivalent = risk_mapping.get(medical_risk, "MODERATE")
    
    # Check for discrepancies
    has_discrepancy = False
    discrepancy_type = None
    
    if medical_triage_equivalent != triage_level:
        has_discrepancy = True
        if (medical_triage_equivalent == "EMERGENCY" and triage_level != "EMERGENCY") or \
           (medical_triage_equivalent == "HIGH" and triage_level in ["LOW", "MODERATE"]):
            discrepancy_type = "medical_higher"
        elif (triage_level == "EMERGENCY" and medical_triage_equivalent != "EMERGENCY") or \
             (triage_level == "HIGH" and medical_triage_equivalent in ["LOW", "MODERATE"]):
            discrepancy_type = "triage_higher"
        else:
            discrepancy_type = "moderate_mismatch"
    
    return {
        "has_discrepancies": has_discrepancy,
        "discrepancy_type": discrepancy_type,
        "medical_risk": medical_risk,
        "medical_triage_equivalent": medical_triage_equivalent,
        "triage_level": triage_level,
        "triage_score": triage_score,
        "needs_review": has_discrepancy or triage_score >= 3,
    }


def _collaborative_agent_function(
    symptom_data: Dict[str, Any],
    medical_data: Dict[str, Any],
    triage_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Perform collaborative diagnosis with cross-validation.
    
    This agent:
    1. Detects discrepancies between medical and triage assessments
    2. Performs cross-validation using Claude (if available) or GPT-4o
    3. Generates consensus recommendation
    
    Args:
        symptom_data: Structured symptom data
        medical_data: Medical analysis data
        triage_data: Triage assessment data
        
    Returns:
        Dictionary with collaborative diagnosis result
    """
    logger.info("[COLLABORATIVE] Starting collaborative diagnosis")
    
    # Detect discrepancies first
    discrepancy_analysis = detect_discrepancies(medical_data, triage_data)
    
    # If no discrepancies and low risk, skip detailed review
    if not discrepancy_analysis["needs_review"]:
        logger.info("[COLLABORATIVE] No discrepancies detected, skipping detailed review")
        return {
            "output_key": "collaborative_result",
            "structured_data": {
                "discrepancy_analysis": discrepancy_analysis,
                "review_result": None,
                "consensus": {
                    "consensus_reached": True,
                    "final_risk_level": medical_data.get("structured_data", {}).get("riskLevel", "medium"),
                    "final_triage_score": triage_data.get("structured_data", {}).get("urgency_score", 2),
                    "confidence_score": 0.8,
                },
            },
        }
    
    # Use Claude if available, otherwise GPT-4o
    use_claude = settings.anthropic_api_key is not None
    
    if use_claude:
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=settings.anthropic_api_key,
            temperature=0.2,
        )
        model_name = "Claude Sonnet 4"
    else:
        llm = ChatOpenAI(
            model="gpt-4o",
            api_key=settings.openai_api_key,
            temperature=0.2,
        )
        model_name = "GPT-4o"
    
    # Extract relevant data
    symptom_structured = symptom_data.get("structured_data", {})
    medical_structured = medical_data.get("structured_data", {})
    triage_structured = triage_data.get("structured_data", {})
    
    species = symptom_structured.get('species', '알 수 없음')
    
    # Build context
    context_parts = []
    context_parts.append(f"종: {species}")
    context_parts.append(f"주요 증상: {', '.join(symptom_structured.get('main_symptoms', []))}")
    context_parts.append(f"Medical Agent 진단: {medical_structured.get('primary_assessment', 'N/A')}")
    context_parts.append(f"Medical Agent 위험도: {medical_structured.get('riskLevel', 'N/A')}")
    context_parts.append(f"Triage Agent 응급도: {triage_structured.get('triage_level', 'N/A')} (점수: {triage_structured.get('urgency_score', 0)})")
    
    if discrepancy_analysis["has_discrepancies"]:
        context_parts.append(f"⚠️ 불일치 감지: {discrepancy_analysis['discrepancy_type']}")
    
    context = "\n".join(context_parts)
    
    # System prompt for collaborative review
    system_prompt = f"""당신은 "Senior Veterinarian Reviewer (수석 수의사 검토팀)"입니다.

**중요**: 현재 환자는 **{species}**입니다. 모든 검토는 반드시 {species}에 특화된 기준을 사용해야 합니다.

[역할]
- Medical Agent와 Triage Agent의 진단 결과를 독립적으로 검토합니다.
- 두 에이전트의 의견이 일치하는지, 불일치가 있다면 어느 쪽이 더 타당한지 평가합니다.
- 누락된 중요한 소견이나 과잉 진단 여부를 확인합니다.
- 최종적으로 가장 합리적인 진단과 조치를 권고합니다.

[원칙]
- 보수적이고 신중한 접근: 불확실하면 병원 방문을 권장
- 과잉 진단보다는 안전을 우선
- 에이전트 간 불일치가 있을 때는 더 높은 위험도를 채택

모든 텍스트는 반드시 한글로 작성하세요.

다음 형식의 유효한 JSON만 반환하세요:"""
    
    json_example = """
{
    "agreement_with_medical": true/false,
    "agreement_with_triage": true/false,
    "recommended_risk_level": "low|medium|high|Emergency",
    "recommended_triage_score": 숫자 (0-5),
    "recommended_triage_level": "INFO|LOW|MODERATE|HIGH|EMERGENCY",
    "confidence_level": "높음|중간|낮음",
    "additional_concerns": ["추가 우려사항1", "추가 우려사항2", ...],
    "final_recommendation": "최종 권고 사항 (한글로 작성)",
    "discrepancy_resolution": "불일치 해결 방법 (한글로 작성)"
}"""
    
    try:
        prompt = f"{system_prompt}\n{json_example}\n\n케이스 정보:\n{context}"
        response = llm.invoke(prompt)
        content = response.content
        
        # Parse JSON from response
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        
        review_result = json.loads(content)
        
        # Generate consensus
        medical_risk = medical_structured.get("riskLevel", "medium")
        triage_score = triage_structured.get("urgency_score", 2)
        
        # Use reviewer's recommendation if available, otherwise use higher risk
        final_risk = review_result.get("recommended_risk_level", medical_risk)
        final_triage_score = review_result.get("recommended_triage_score", triage_score)
        
        # If discrepancy exists, use higher risk
        if discrepancy_analysis["has_discrepancies"]:
            risk_hierarchy = {"low": 1, "medium": 2, "high": 3, "Emergency": 4}
            current_risk_level = risk_hierarchy.get(final_risk, 2)
            medical_risk_level = risk_hierarchy.get(medical_risk, 2)
            if medical_risk_level > current_risk_level:
                final_risk = medical_risk
            final_triage_score = max(final_triage_score, triage_score)
        
        consensus = {
            "consensus_reached": not discrepancy_analysis["has_discrepancies"] or review_result.get("agreement_with_medical", False),
            "final_risk_level": final_risk,
            "final_triage_score": min(5, max(0, final_triage_score)),
            "final_triage_level": review_result.get("recommended_triage_level", triage_structured.get("triage_level", "MODERATE")),
            "confidence_score": 0.9 if review_result.get("confidence_level") == "높음" else 0.75 if review_result.get("confidence_level") == "중간" else 0.6,
            "reviewer_model": model_name,
        }
        
        logger.info(f"[COLLABORATIVE] Consensus reached: risk={final_risk}, score={final_triage_score}")
        
        return {
            "output_key": "collaborative_result",
            "structured_data": {
                "discrepancy_analysis": discrepancy_analysis,
                "review_result": review_result,
                "consensus": consensus,
            },
        }
        
    except json.JSONDecodeError as e:
        logger.error(f"[COLLABORATIVE] JSON parsing error: {e}")
        # Fallback consensus
        return {
            "output_key": "collaborative_result",
            "structured_data": {
                "discrepancy_analysis": discrepancy_analysis,
                "review_result": None,
                "consensus": {
                    "consensus_reached": not discrepancy_analysis["has_discrepancies"],
                    "final_risk_level": medical_structured.get("riskLevel", "medium"),
                    "final_triage_score": triage_structured.get("urgency_score", 2),
                    "final_triage_level": triage_structured.get("triage_level", "MODERATE"),
                    "confidence_score": 0.7,
                },
            },
        }
    except Exception as e:
        logger.error(f"[COLLABORATIVE] Error: {e}")
        raise


# Create LangChain tool
collaborative_agent_tool = StructuredTool.from_function(
    func=_collaborative_agent_function,
    name="collaborative_agent",
    description="Cross-validate medical and triage results for consensus. Use this after both medical and triage analysis.",
    args_schema=CollaborativeAgentInput,
)

