"""
Тесты логики ранжирования (scoring) — чистая математика без БД и API
"""
import pytest
from app.bot.logic.scoring import (
    calculate_age_score,
    calculate_city_score,
    calculate_interests_score,
    calculate_candidate_score,
    WEIGHTS
)


class TestAgeScore:
    """Тесты расчета возрастного скора"""
    
    def test_perfect_age_match(self):
        """Тест: возраст точно в середине диапазона"""
        class MockCriteria:
            age_from = 20
            age_to = 30
        
        score = calculate_age_score(MockCriteria(), 25)
        assert score == 1.0
    
    def test_age_near_range(self):
        """Тест: возраст близко к диапазону"""
        class MockCriteria:
            age_from = 20
            age_to = 30
        
        score = calculate_age_score(MockCriteria(), 22)
        assert 0.5 < score < 1.0
    
    def test_age_at_lower_boundary(self):
        """Тест: возраст на нижней границе"""
        class MockCriteria:
            age_from = 20
            age_to = 30
        
        score = calculate_age_score(MockCriteria(), 20)
        # Должен быть выше 0, но не 1.0
        assert 0.0 < score < 1.0
    
    def test_age_at_upper_boundary(self):
        """Тест: возраст на верхней границе"""
        class MockCriteria:
            age_from = 20
            age_to = 30
        
        score = calculate_age_score(MockCriteria(), 30)
        assert 0.0 < score < 1.0
    
    def test_age_out_of_range(self):
        """Тест: возраст вне диапазона"""
        class MockCriteria:
            age_from = 20
            age_to = 30
        
        score = calculate_age_score(MockCriteria(), 35)
        assert score == 0.0
    
    def test_age_missing(self):
        """Тест: возраст не указан"""
        class MockCriteria:
            age_from = 20
            age_to = 30
        
        score = calculate_age_score(MockCriteria(), None)
        assert score == 0.0
    
    def test_single_age_value(self):
        """Тест: только один возраст (age_from == age_to)"""
        class MockCriteria:
            age_from = 25
            age_to = 25
        
        score = calculate_age_score(MockCriteria(), 25)
        assert score == 1.0
        
        score = calculate_age_score(MockCriteria(), 26)
        assert score == 0.0


class TestCityScore:
    """Тесты расчета скора города"""
    
    def test_city_match(self):
        """Тест: город совпадает"""
        class MockCriteria:
            city = "Москва"
        
        score = calculate_city_score(MockCriteria(), "Москва")
        assert score == 1.0
    
    def test_city_mismatch(self):
        """Тест: город не совпадает"""
        class MockCriteria:
            city = "Москва"
        
        score = calculate_city_score(MockCriteria(), "Санкт-Петербург")
        assert score == 0.0
    
    def test_city_not_specified(self):
        """Тест: город не указан в критериях"""
        class MockCriteria:
            city = None
        
        score = calculate_city_score(MockCriteria(), "Москва")
        assert score == 0.0


class TestInterestsScore:
    """Тесты расчета скора интересов"""
    
    def test_perfect_interests_match(self, db_session, test_user):
        """Тест: полное совпадение интересов"""
        class MockCandidate:
            vk_id = 999999
        
        # Мокаем calculate_interest_overlap
        with pytest.MonkeyPatch().context() as mp:
            def mock_overlap(*args, **kwargs):
                return {
                    'music': 3,
                    'books': 2,
                    'groups': 5,
                    'total': 10
                }
            
         
            mp.setattr('app.bot.logic.scoring.calculate_interest_overlap', mock_overlap)
            
            score = calculate_interests_score(db_session, test_user.vk_id, MockCandidate().vk_id)
            # Скор должен быть между 0 и 1
            assert 0.0 < score <= 1.0
    
    def test_no_interests_match(self, db_session, test_user):
        """Тест: нет совпадения интересов"""
        class MockCandidate:
            vk_id = 999999
        
        with pytest.MonkeyPatch().context() as mp:
            def mock_overlap(*args, **kwargs):
                return {
                    'music': 0,
                    'books': 0,
                    'groups': 0,
                    'total': 0
                }
            
            
            mp.setattr('app.bot.logic.scoring.calculate_interest_overlap', mock_overlap)
            
            score = calculate_interests_score(db_session, test_user.vk_id, MockCandidate().vk_id)
            assert score == 0.0


class TestCandidateScore:
    """Тесты полного расчета скора кандидата"""
    
    def test_perfect_candidate(self):
        """Тест: идеальный кандидат (все компоненты на 100%)"""
        class MockCriteria:
            age_from = 20
            age_to = 30
            city = "Москва"
        
        class MockCandidate:
            age = 25
            city = "Москва"
            vk_id = 999999
        
        class MockDB:
            pass
        
        db_mock = MockDB()
        
        with pytest.MonkeyPatch().context() as mp:
            def mock_interests_score(*args, **kwargs):
                return 1.0
            
            mp.setattr('app.bot.logic.scoring.calculate_interests_score', mock_interests_score)
            mp.setattr('app.bot.logic.scoring.calculate_friends_score', lambda *args: 1.0)
            
            score = calculate_candidate_score(
                db_mock, 
                123456, 
                MockCandidate(), 
                MockCriteria()
            )
            
            expected = WEIGHTS['age'] + WEIGHTS['city'] + WEIGHTS['interests'] + WEIGHTS['friends']
            assert score == pytest.approx(expected, 0.01)
    
    def test_candidate_with_common_interests(self):
        """Тест: кандидат с общими интересами получает больше баллов"""
        class MockCriteria:
            age_from = 20
            age_to = 30
            city = "Москва"
        
        class MockCandidate:
            age = 25
            city = "Москва"
            vk_id = 999999
        
        db_mock = object()
        
        scores = []
        
        with pytest.MonkeyPatch().context() as mp:
            def mock_interests_score_factory(value):
                return lambda *args: value
            
            # Скор с хорошим совпадением интересов
            mp.setattr('app.bot.logic.scoring.calculate_interests_score', 
                       mock_interests_score_factory(0.8))
            score_high = calculate_candidate_score(db_mock, 123456, MockCandidate(), MockCriteria())
            scores.append(score_high)
            
            # Скор с плохим совпадением интересов
            mp.setattr('app.bot.logic.scoring.calculate_interests_score', 
                       mock_interests_score_factory(0.2))
            score_low = calculate_candidate_score(db_mock, 123456, MockCandidate(), MockCriteria())
            scores.append(score_low)
        
        assert scores[0] > scores[1]
    
    def test_zero_candidate(self):
        """Тест: кандидат с нулевым совпадением"""
        class MockCriteria:
            age_from = 20
            age_to = 30
            city = "Москва"
        
        class MockCandidate:
            age = 40
            city = "Новосибирск"
            vk_id = 999999
        
        db_mock = object()
        
        with pytest.MonkeyPatch().context() as mp:
            def mock_interests_score(*args, **kwargs):
                return 0.0
            
            mp.setattr('app.bot.logic.scoring.calculate_interests_score', mock_interests_score)
            mp.setattr('app.bot.logic.scoring.calculate_friends_score', lambda *args: 0.0)
            
            score = calculate_candidate_score(db_mock, 123456, MockCandidate(), MockCriteria())
            assert score == 0.0
    
    def test_score_with_missing_data(self):
        """Тест: кандидат с отсутствующими данными (возраст и город не указаны)"""
        class MockCriteria:
            age_from = 20
            age_to = 30
            city = "Москва"
        
        class MockCandidate:
            age = None
            city = None
            vk_id = 999999
        
        db_mock = object()
        
        with pytest.MonkeyPatch().context() as mp:
            def mock_interests_score(*args, **kwargs):
                return 0.5
            
            mp.setattr('app.bot.logic.scoring.calculate_interests_score', mock_interests_score)
            mp.setattr('app.bot.logic.scoring.calculate_friends_score', lambda *args: 0.0)
            
            # Не должно быть ошибки
            score = calculate_candidate_score(db_mock, 123456, MockCandidate(), MockCriteria())
            assert score >= 0.0