from typing import Dict, Any, List, Optional, Tuple
import re


def _parse_bucket_label(label: str) -> Tuple[int, Optional[int]]:
    """Parse bucket labels like '800-1000' or '3000+' into (low, high).
    Returns (low, high) where high is None for open-ended buckets.
    """
    m = re.match(r"^(\d+)-(\d+)$", label)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.match(r"^(\d+)\+$", label)
    if m:
        return int(m.group(1)), None
    return (0, None)


def generate_user_insights(
    tag_stats: Dict[str, Dict[str, Any]],
    rating_stats: Dict[str, Dict[str, Any]],
    solve_time_stats: Optional[float],
) -> List[str]:
    """Generate deterministic human-readable insights from analysis results.

    Inputs:
      - tag_stats: mapping tag -> {attempted:int, solved:int, accuracy:float}
      - rating_stats: mapping bucket_label -> {attempted:int, solved:int, success_rate:float}
      - solve_time_stats: average solve time in milliseconds (or None)

    Rules (deterministic):
      - Tags with accuracy < 40% and at least 3 attempts are marked as weak.
      - If rating bucket success drops by >=25 percentage points between consecutive
        buckets (with at least 5 attempts in the higher bucket) we flag a difficulty ceiling.
      - If average solve time > 20 minutes we flag inefficiency; > 60 minutes flagged severe.
    """
    insights: List[str] = []

    # 1) Weak tags
    TAG_ATTEMPT_THRESHOLD = 3
    WEAK_ACCURACY_THRESHOLD = 0.40
    weak_tags = []
    for tag, stats in tag_stats.items():
        attempted = int(stats.get("attempted", 0))
        accuracy = float(stats.get("accuracy", 0.0))
        if attempted >= TAG_ATTEMPT_THRESHOLD and accuracy < WEAK_ACCURACY_THRESHOLD:
            weak_tags.append((tag, attempted, accuracy))

    if weak_tags:
        # sort by accuracy ascending
        weak_tags.sort(key=lambda t: t[2])
        tag_list = ", ".join(f"{t[0]} ({int(t[2]*100)}% over {t[1]} attempts)" for t in weak_tags[:6])
        insights.append(f"Weak tags: {tag_list}.")

    # 2) Difficulty ceiling from rating buckets
    # Build ordered list of buckets by lower bound
    bucket_items: List[Tuple[int, str, float, int]] = []  # (low, label, success_rate, attempted)
    for label, stats in rating_stats.items():
        low, _ = _parse_bucket_label(label)
        success = float(stats.get("success_rate", 0.0))
        attempted = int(stats.get("attempted", 0))
        bucket_items.append((low, label, success, attempted))

    bucket_items.sort(key=lambda x: x[0])
    CEILING_DROP = 0.25
    ATTEMPTED_MIN = 5
    ceiling_flagged = False
    for i in range(1, len(bucket_items)):
        prev = bucket_items[i - 1]
        cur = bucket_items[i]
        prev_rate = prev[2]
        cur_rate = cur[2]
        cur_attempts = cur[3]
        # absolute drop
        if cur_attempts >= ATTEMPTED_MIN and (prev_rate - cur_rate) >= CEILING_DROP:
            insights.append(
                f"Difficulty ceiling around {cur[1]}: success rate drops from {int(prev_rate*100)}% to {int(cur_rate*100)}%.")
            ceiling_flagged = True
            break

    # 3) Solve time inefficiency
    if solve_time_stats is not None:
        mins = solve_time_stats / 1000.0 / 60.0
        if mins > 60:
            insights.append(f"Average solve time is high: {mins:.0f} minutes — consider focused practice to reduce time.")
        elif mins > 20:
            insights.append(f"Average solve time is above typical expectations: {mins:.0f} minutes.")

    if not insights:
        insights.append("No major issues detected — keep up the steady progress.")

    return insights
