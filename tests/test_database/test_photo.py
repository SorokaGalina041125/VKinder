import pytest
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from psycopg.errors import NotNullViolation, ForeignKeyViolation

from app.database.models.user import User
from app.database.models.photo import Photo


class TestPhotoModel:
    """Тесты для модели Photo"""

    def test_create_photo(self, session, clean_db, test_user):
        """Тест создания фотографии"""
        photo = Photo(
            user_vk_id=test_user.vk_id,
            photo_id="photo_123456",
            owner_id=test_user.vk_id,
            photo_url="https://vk.com/photo123456",
            likes_count=150,
            comments_count=10,
            is_profile_photo=True,
            popularity_score=150
        )
        
        session.add(photo)
        session.commit()
        session.refresh(photo)
        
        assert photo.id is not None
        assert photo.user_vk_id == test_user.vk_id
        assert photo.photo_id == "photo_123456"
        assert photo.owner_id == test_user.vk_id
        assert photo.photo_url == "https://vk.com/photo123456"
        assert photo.likes_count == 150
        assert photo.comments_count == 10
        assert photo.is_profile_photo is True
        assert photo.popularity_score == 150
        assert isinstance(photo.created_at, datetime)

    def test_create_photo_with_defaults(self, session, clean_db, test_user):
        """Тест создания фотографии со значениями по умолчанию"""
        photo = Photo(
            user_vk_id=test_user.vk_id,
            photo_id="photo_789012",
            owner_id=test_user.vk_id,
            photo_url="https://vk.com/photo789012"
        )
        
        session.add(photo)
        session.commit()
        session.refresh(photo)
        
        assert photo.likes_count == 0
        assert photo.comments_count == 0
        assert photo.is_profile_photo is False
        assert photo.popularity_score == 0
        assert isinstance(photo.created_at, datetime)

    def test_create_multiple_photos(self, session, clean_db, test_user):
        """Тест создания нескольких фотографий для одного пользователя"""
        photos = [
            Photo(
                user_vk_id=test_user.vk_id,
                photo_id="photo_1",
                owner_id=test_user.vk_id,
                photo_url="url1",
                likes_count=100,
                is_profile_photo=True
            ),
            Photo(
                user_vk_id=test_user.vk_id,
                photo_id="photo_2",
                owner_id=test_user.vk_id,
                photo_url="url2",
                likes_count=200
            ),
            Photo(
                user_vk_id=test_user.vk_id,
                photo_id="photo_3",
                owner_id=test_user.vk_id,
                photo_url="url3",
                likes_count=300
            ),
        ]
        
        session.add_all(photos)
        session.commit()
        
        user_photos = session.query(Photo).filter_by(user_vk_id=test_user.vk_id).all()
        assert len(user_photos) == 3
        
        popular_photos = session.query(Photo).filter_by(
            user_vk_id=test_user.vk_id
        ).order_by(Photo.likes_count.desc()).all()
        
        assert popular_photos[0].likes_count == 300
        assert popular_photos[1].likes_count == 200
        assert popular_photos[2].likes_count == 100

    def test_foreign_key_constraint(self, session, clean_db):
        """Тест внешнего ключа - нельзя добавить фото с несуществующим пользователем"""
        photo = Photo(
            user_vk_id=99999,
            photo_id="photo_123",
            owner_id=99999,
            photo_url="url"
        )
        
        session.add(photo)
        
        with pytest.raises(IntegrityError) as excinfo:
            session.commit()
        
        assert isinstance(excinfo.value.orig, ForeignKeyViolation)
        session.rollback()

    def test_get_user_photos(self, session, clean_db, test_user):
        """Тест получения всех фотографий пользователя"""
        photos = [
            Photo(
                user_vk_id=test_user.vk_id,
                photo_id=f"photo_{i}",
                owner_id=test_user.vk_id,
                photo_url=f"url{i}",
                likes_count=i*100
            )
            for i in range(1, 6)
        ]
        
        session.add_all(photos)
        session.commit()
        
        user_photos = session.query(Photo).filter_by(user_vk_id=test_user.vk_id).all()
        assert len(user_photos) == 5

    def test_delete_photo(self, session, clean_db, test_user):
        """Тест удаления фотографии"""
        photo = Photo(
            user_vk_id=test_user.vk_id,
            photo_id="photo_to_delete",
            owner_id=test_user.vk_id,
            photo_url="url"
        )
        
        session.add(photo)
        session.commit()
        
        photo_id = photo.id
        session.delete(photo)
        session.commit()
        
        deleted_photo = session.get(Photo, photo_id)
        assert deleted_photo is None

    def test_update_photo_metrics(self, session, clean_db, test_user):
        """Тест обновления метрик фотографии"""
        photo = Photo(
            user_vk_id=test_user.vk_id,
            photo_id="photo_123",
            owner_id=test_user.vk_id,
            photo_url="url",
            likes_count=100,
            comments_count=5
        )
        
        session.add(photo)
        session.commit()
        
        photo.likes_count = 200
        photo.comments_count = 15
        photo.popularity_score = 200
        session.commit()
        session.refresh(photo)
        
        assert photo.likes_count == 200
        assert photo.comments_count == 15
        assert photo.popularity_score == 200

    def test_photo_repr(self, session, clean_db, test_user):
        """Тест строкового представления"""
        photo = Photo(
            user_vk_id=test_user.vk_id,
            photo_id="photo_123",
            owner_id=test_user.vk_id,
            photo_url="url",
            likes_count=150
        )
        
        expected_repr = "<Photo(id=photo_123, likes=150)>"
        assert repr(photo) == expected_repr

    def test_cannot_delete_user_with_photos(self, session, clean_db, test_user):
        """Тест что нельзя удалить пользователя, у которого есть фотографии (защита от потери данных)"""
        # Создаем фото
        photo = Photo(
            user_vk_id=test_user.vk_id,
            photo_id="photo_123",
            owner_id=test_user.vk_id,
            photo_url="url"
        )
        session.add(photo)
        session.commit()
        
        # Пытаемся удалить пользователя
        user = session.get(User, test_user.vk_id)
        session.delete(user)
        
        # Должна возникнуть ошибка NOT NULL (SQLAlchemy пытается обновить внешний ключ)
        with pytest.raises(IntegrityError) as excinfo:
            session.commit()
        
        # Проверяем что это ошибка NotNullViolation (а не ForeignKeyViolation)
        assert isinstance(excinfo.value.orig, NotNullViolation)
        assert "user_vk_id" in str(excinfo.value.orig).lower()
        
        session.rollback()
        
        # Проверяем что пользователь и фото всё еще в базе
        assert session.get(User, test_user.vk_id) is not None
        assert session.query(Photo).filter_by(user_vk_id=test_user.vk_id).count() == 1

    def test_delete_photos_before_user(self, session, clean_db, test_user):
        """Тест что можно удалить пользователя после удаления его фотографий"""
        # Создаем фото
        photo = Photo(
            user_vk_id=test_user.vk_id,
            photo_id="photo_123",
            owner_id=test_user.vk_id,
            photo_url="url"
        )
        session.add(photo)
        session.commit()
        
        # Сначала удаляем все фото пользователя
        session.query(Photo).filter_by(user_vk_id=test_user.vk_id).delete()
        session.commit()
        
        # Теперь можно удалить пользователя
        user = session.get(User, test_user.vk_id)
        session.delete(user)
        session.commit()
        
        # Проверяем что пользователь удален
        assert session.get(User, test_user.vk_id) is None
        assert session.query(Photo).filter_by(user_vk_id=test_user.vk_id).count() == 0