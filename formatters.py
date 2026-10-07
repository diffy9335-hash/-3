"""Форматтеры вывода."""

def fmt_resources(r) -> str:
    return (
        f"💵 Деньги: {r.money}\n"
        f"🌾 Еда: {r.food}\n"
        f"⛏️ Железо: {r.iron}\n"
        f"🛢️ Нефть: {r.oil}\n"
        f"🔬 Наука: {r.science}\n"
        f"👥 Население: {r.population}\n"
        f"⚡ Энергия: {r.energy}\n"
        f"🏭 Промышленность: {r.industry}"
    )


def progress_bar(done: int, total: int, length: int = 10) -> str:
    filled = int(length * done / total) if total else 0
    return "▓" * filled + "░" * (length - filled)
