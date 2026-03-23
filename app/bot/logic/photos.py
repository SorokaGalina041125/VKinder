def sort_photos(photos):
    """
    Сортировка фотографий по популярности (лайки + комментарии).
    Возвращает топ-3 фотографии.
    """
    sorted_photos = sorted(
        photos,
        key=lambda x: x.get('likes', {}).get('count', 0) + x.get('comments', {}).get('count', 0),
        reverse=True
    )
    return sorted_photos[:3]


def get_top_photos(photos, count=3):
    """Получение топ-N фотографий"""
    return sort_photos(photos)[:count]