"""FAQ Service - Provides related FAQ data based on symptoms and species."""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


# FAQ 데이터 구조 (Firebase에서 가져올 예정)
# 현재는 하드코딩된 예시 데이터 사용
FAQ_EXAMPLES = [
    {
        "species_code": "dog",
        "symptom_tag": "itching",
        "question_ko": "우리 강아지가 몸을 계속 긁는데 알레르기일까요?",
        "answer_ko": "강아지가 몸을 자주 긁는다면 알레르기, 피부염, 기생충 감염 등이 원인일 수 있어요. 긁는 부위가 붉거나 털이 빠지면 1~2일 내로 병원 진료를 권장합니다.",
        "keywords": ["가려움", "긁기", "알레르기", "피부"],
    },
    {
        "species_code": "dog",
        "symptom_tag": "vomiting",
        "question_ko": "강아지가 계속 토하는데 어떻게 해야 하나요?",
        "answer_ko": "구토가 3회 이상 지속되거나 혈액이 섞여 있으면 즉시 병원 방문이 필요합니다. 경미한 경우 12시간 금식 후 소량의 물부터 제공하세요.",
        "keywords": ["구토", "토함", "위장"],
    },
    {
        "species_code": "cat",
        "symptom_tag": "lethargy",
        "question_ko": "고양이가 무기력한데 괜찮을까요?",
        "answer_ko": "무기력은 다양한 질병의 초기 증상일 수 있어요. 24시간 이상 지속되거나 다른 증상과 함께 나타나면 수의사 진료를 권장합니다.",
        "keywords": ["무기력", "활동량", "기운없음"],
    },
]


def get_related_faqs(
    symptoms: List[str],
    species: Optional[str] = None,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Get related FAQs based on symptoms and species.
    
    Args:
        symptoms: List of symptoms
        species: Pet species (optional)
        limit: Maximum number of FAQs to return
        
    Returns:
        List of related FAQ dictionaries
    """
    logger.info(f"[FAQ] Getting FAQs for symptoms: {symptoms}, species: {species}")
    
    symptom_keywords = " ".join(symptoms).lower()
    matched_faqs = []
    
    for faq in FAQ_EXAMPLES:
        # Species filter
        if species and faq.get("species_code") != species.lower():
            continue
        
        # Keyword matching
        faq_text = f"{faq.get('question_ko', '')} {faq.get('answer_ko', '')} {' '.join(faq.get('keywords', []))}".lower()
        
        score = 0
        for keyword in symptom_keywords.split():
            if keyword in faq_text:
                score += 1
        
        if score > 0:
            matched_faqs.append({
                **faq,
                "relevance_score": score,
            })
    
    # Sort by relevance score
    matched_faqs.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    return matched_faqs[:limit]


def generate_recommended_questions(
    symptoms: List[str],
    diagnosis: Optional[str] = None,
    species: Optional[str] = None,
) -> List[Dict[str, str]]:
    """Generate recommended follow-up questions based on symptoms and diagnosis.
    
    Args:
        symptoms: List of symptoms
        diagnosis: Primary diagnosis (optional)
        species: Pet species (optional)
        
    Returns:
        List of recommended questions with IDs
    """
    logger.info(f"[FAQ] Generating recommended questions for: {symptoms}")
    
    # Generate questions based on symptoms
    question_templates = {
        "구토": [
            {"id": "vomiting_frequency", "question": "구토는 하루에 몇 회 정도 발생하나요?"},
            {"id": "vomiting_content", "question": "구토물에 혈액이나 이상한 색이 섞여 있나요?"},
            {"id": "vomiting_timing", "question": "구토는 식사 전후 언제 주로 발생하나요?"},
        ],
        "설사": [
            {"id": "diarrhea_duration", "question": "설사가 시작된 지 얼마나 되었나요?"},
            {"id": "diarrhea_consistency", "question": "설사는 묽은 형태인가요, 아니면 점액이나 혈액이 섞여 있나요?"},
            {"id": "diarrhea_frequency", "question": "하루에 몇 회 정도 설사를 하나요?"},
        ],
        "가려움": [
            {"id": "itching_location", "question": "가려워하는 부위가 어디인가요?"},
            {"id": "itching_severity", "question": "가려움으로 인해 피부가 상처가 나거나 털이 빠졌나요?"},
            {"id": "itching_timing", "question": "가려움은 특정 시간대나 상황에서 더 심해지나요?"},
        ],
        "무기력": [
            {"id": "lethargy_duration", "question": "무기력한 상태가 얼마나 지속되었나요?"},
            {"id": "lethargy_activity", "question": "평소에 좋아하던 활동에도 관심이 없나요?"},
            {"id": "lethargy_appetite", "question": "식욕은 정상인가요?"},
        ],
    }
    
    recommended = []
    for symptom in symptoms:
        if symptom in question_templates:
            recommended.extend(question_templates[symptom][:1])  # Take first question from each category
    
    # If no specific questions found, provide generic ones
    if not recommended:
        recommended = [
            {"id": "symptom_duration", "question": "증상이 시작된 지 얼마나 되었나요?"},
            {"id": "symptom_severity", "question": "증상이 점점 심해지고 있나요, 아니면 호전되고 있나요?"},
            {"id": "other_symptoms", "question": "다른 이상 증상도 함께 나타나고 있나요?"},
        ]
    
    return recommended[:3]  # Return top 3

