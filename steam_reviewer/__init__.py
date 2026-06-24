"""steam-reviewer — Steam 리뷰 수집·분석·요약 도구."""

__version__ = "0.3.0"

from .loaders.steam import resolve_appid, fetch_reviews, reviews_dataframe
from .analyzers.basic import analyze_basic
from .analyzers.keywords import analyze_keywords
from .analyzers.trends import analyze_trends
from .analyzers.distributions import analyze_distributions
from .cache import ReviewCache, fetch_reviews_cached
from .ai.summarize import summarize_reviews, AISummaryUnavailable

__all__ = [
    "__version__",
    "resolve_appid",
    "fetch_reviews",
    "reviews_dataframe",
    "analyze_basic",
    "analyze_keywords",
    "analyze_trends",
    "analyze_distributions",
    "ReviewCache",
    "fetch_reviews_cached",
    "summarize_reviews",
    "AISummaryUnavailable",
]
