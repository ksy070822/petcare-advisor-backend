"""Medication Service - Provides medication guidance based on medicationLogs data and symptoms."""

import logging
from typing import Dict, Any, List, Optional
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


# 약물 로그 데이터 구조 (Firebase에서 가져올 예정)
# 현재는 하드코딩된 예시 데이터 사용
MEDICATION_EXAMPLES = [
    {
        "medication": {"name": "항생제", "dosage": "1일 1회", "duration": "5일분", "usage": "식전 30분"},
        "evaluation": {"effectivenessRating": 5, "sideEffectLevel": 2},
        "symptoms": ["구토", "설사", "감염"],
    },
    {
        "medication": {"name": "위장보호제", "dosage": "1일 2회", "duration": "5일분", "usage": "식전 30분"},
        "evaluation": {"effectivenessRating": 4, "sideEffectLevel": 1},
        "symptoms": ["구토", "위장", "소화불량"],
    },
    {
        "medication": {"name": "아포퀠정", "dosage": "1일 1회", "duration": "10일분", "usage": "식후 30분"},
        "evaluation": {"effectivenessRating": 4, "sideEffectLevel": 2},
        "symptoms": ["피부", "가려움", "알레르기"],
    },
]


def get_medication_guidance(
    symptoms: List[str],
    diagnosis: Optional[str] = None,
    species: Optional[str] = None,
) -> Dict[str, Any]:
    """Get medication guidance based on symptoms and diagnosis.
    
    Args:
        symptoms: List of symptoms
        diagnosis: Primary diagnosis (optional)
        species: Pet species (optional)
        
    Returns:
        Dictionary with medication guidance
    """
    logger.info(f"[MEDICATION] Getting guidance for symptoms: {symptoms}")
    
    # Simple matching logic (in production, this would query Firebase)
    matched_medications = []
    
    symptom_keywords = " ".join(symptoms).lower()
    
    for med_example in MEDICATION_EXAMPLES:
        med_symptoms = " ".join(med_example.get("symptoms", [])).lower()
        
        # Simple keyword matching
        if any(keyword in med_symptoms for keyword in symptom_keywords.split()):
            matched_medications.append(med_example)
    
    if not matched_medications:
        # Default guidance
        return {
            "has_medication_guidance": False,
            "medication_types": [],
            "general_guidance": "증상에 따라 수의사가 적절한 약물을 처방할 수 있습니다. 자가 투약은 권장하지 않습니다.",
        }
    
    # Get most effective medication
    best_med = max(matched_medications, key=lambda x: x.get("evaluation", {}).get("effectivenessRating", 0))
    
    medication_types = []
    for med in matched_medications[:3]:  # Top 3
        med_info = med.get("medication", {})
        medication_types.append({
            "name": med_info.get("name", ""),
            "typical_usage": f"{med_info.get('dosage', '')} {med_info.get('usage', '')}",
            "effectiveness": med.get("evaluation", {}).get("effectivenessRating", 0),
        })
    
    return {
        "has_medication_guidance": True,
        "medication_types": medication_types,
        "recommended_type": best_med.get("medication", {}).get("name", ""),
        "general_guidance": f"{best_med.get('medication', {}).get('name', '약물')} 종류의 약으로 호전될 수 있어요. 수의사와 상의하여 적절한 처방을 받으시기 바랍니다.",
    }

