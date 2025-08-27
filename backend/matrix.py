# backend/matrix.py
# В этом контексте, "матрица" — это не рынок, а матрица возможных состояний и советов.

def generate_insight(gene: dict) -> dict:
    """
    Генерирует "инсайт" и рекомендацию на основе параметров гена.
    Это — ядро нашего "AI-тренера для души".
    """

    # --- Логика генерации инсайта ---
    # Это простая система правил, но она создает иллюзию глубокого понимания.

    summary_parts = []
    if gene['complexity'] > 0.7:
        summary_parts.append("Your thoughts seem to be structured and complex.")
    elif gene['complexity'] < 0.3:
        summary_parts.append("Your expression is direct and to the point.")

    if gene['richness'] > 0.8:
        summary_parts.append("You are using a rich and diverse vocabulary.")

    if gene['rhythm'] > 0.7:
        summary_parts.append("There's a consistent, steady rhythm to your words.")

    if gene['sentiment'] > 0.6:
        summary_parts.append("A strong emotional undercurrent is present.")
    elif gene['sentiment'] < 0.4:
        summary_parts.append("Your tone appears to be calm and measured.")

    # --- Логика генерации рекомендации ---
    action = "Consider taking a few deep breaths to center yourself." # Действие по умолчанию
    if gene['complexity'] > 0.7 and gene['sentiment'] > 0.6:
        action = "Your mind is working hard. A short, unguided meditation might help process these complex feelings."
    elif gene['rhythm'] < 0.4:
        action = "Your thoughts seem scattered. Try a grounding exercise, focusing on your physical sensations."
    elif gene['sentiment'] < 0.3:
        action = "This is a moment of calm. It's a good opportunity for a gratitude journaling session."

    summary = " ".join(summary_parts) if summary_parts else "You've expressed a balanced state of mind."

    return {
        "summary": summary,
        "recommended_action": action,
        "gene_used": gene
    }
