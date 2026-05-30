from app.data.preprocessor import preprocess_dataset
from app.data.repository import RestaurantRepository

__all__ = ["preprocess_dataset", "RestaurantRepository"]


def load_raw_dataset(*args, **kwargs):
    """Lazy import to avoid side effects when running ``python -m app.data``."""
    from app.data.loader import load_raw_dataset as _load

    return _load(*args, **kwargs)
