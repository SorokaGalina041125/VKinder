# Схема базы данных VKinder

Ниже текстовая ER-схема основных таблиц и связей проекта.

```mermaid
erDiagram
    USERS ||--o| SEARCH_CRITERIA : "has criteria"
    USERS ||--o{ VIEWED_USERS : "views / favorites / blocks"
    USERS ||--o{ PHOTOS : "owns photos"
    USERS ||--o{ USER_INTERESTS : "has interests"
    USERS ||--o{ LIKES : "puts likes"

    USERS {
        int vk_id PK
        string first_name
        string last_name
        int age
        string city
        int sex
        string profile_url
        bool is_bot_user
        string state
        bool is_active
        datetime created_at
    }

    SEARCH_CRITERIA {
        int id PK
        int user_vk_id FK
        int age_from
        int age_to
        int city_id
        string city
        int sex
        bool has_photos
        string relation_status
        int search_offset
        datetime created_at
    }

    VIEWED_USERS {
        int id PK
        int user_vk_id FK
        int candidate_vk_id FK
        bool is_viewed
        bool is_favorite
        bool is_blocked
        datetime viewed_at
    }

    PHOTOS {
        int id PK
        int user_vk_id FK
        int owner_id
        string photo_id
        string photo_url
        int likes_count
        int comments_count
        bool is_profile_photo
        int popularity_score
    }

    USER_INTERESTS {
        int id PK
        int user_vk_id FK
        string interest_type
        string interest_value
        string interest_source_id
    }

    LIKES {
        int id PK
        int user_vk_id FK
        int photo_owner_id
        string photo_id
        datetime created_at
    }
```

Кратко по логике:
- `users` хранит и пользователей бота, и найденных кандидатов (`is_bot_user` отличает тип записи).
- `search_criteria` содержит активные критерии поиска для пользователя бота.
- `viewed_users` объединяет просмотр, избранное и черный список.
- `photos` хранит отобранные фото кандидатов.
- `user_interests` хранит нормализованные интересы по типам (`groups`, `music`, `books`).
- `likes` фиксирует лайки пользователя по фотографиям кандидатов.
