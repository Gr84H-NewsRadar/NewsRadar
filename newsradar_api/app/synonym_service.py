from typing import List
import logging

logger = logging.getLogger(__name__)

# Simple synonym dictionary for common Spanish news terms
SYNONYM_DICT = {
    "economía": ["finanzas", "mercado", "comercio", "negocios", "bolsa"],
    "política": ["gobierno", "elecciones", "parlamento", "congreso", "senado"],
    "tecnología": ["innovación", "digital", "software", "hardware", "internet"],
    "salud": ["medicina", "hospital", "enfermedad", "tratamiento", "sanidad"],
    "deporte": ["fútbol", "baloncesto", "atletismo", "competición", "campeonato"],
    "cultura": ["arte", "música", "teatro", "cine", "literatura"],
    "educación": ["escuela", "universidad", "estudiante", "profesor", "enseñanza"],
    "medio ambiente": ["ecología", "clima", "sostenibilidad", "contaminación", "naturaleza"],
    "ciencia": ["investigación", "experimento", "descubrimiento", "laboratorio", "científico"],
    "sociedad": ["comunidad", "población", "ciudadano", "social", "público"],
}


def get_synonyms(keyword: str, min_count: int = 3, max_count: int = 10) -> List[str]:
    """Get synonym recommendations for a keyword"""
    keyword_lower = keyword.lower().strip()
    
    # Check if keyword exists in dictionary
    if keyword_lower in SYNONYM_DICT:
        synonyms = SYNONYM_DICT[keyword_lower][:max_count]
        return synonyms
    
    # Check if keyword is similar to any key
    for key, values in SYNONYM_DICT.items():
        if keyword_lower in key or key in keyword_lower:
            return values[:max_count]
        if keyword_lower in values:
            result = [key] + [v for v in values if v != keyword_lower]
            return result[:max_count]
    
    # Return empty list if no synonyms found
    return []


def expand_keywords(keywords: List[str], min_synonyms: int = 3, max_synonyms: int = 10) -> dict:
    """Expand a list of keywords with synonyms"""
    expanded = {}
    
    for keyword in keywords:
        synonyms = get_synonyms(keyword, min_synonyms, max_synonyms)
        if synonyms:
            expanded[keyword] = synonyms
        else:
            expanded[keyword] = []
    
    return expanded
