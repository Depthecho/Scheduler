import unittest
from unittest.mock import patch, Mock
from scheduler import Scheduler


class TestScheduler(unittest.TestCase):
    @patch('requests.get')
    def setUp(self, mock_get):
        mock_data = {
            "days": [
                {"id": 1, "date": "2024-10-10", "start": "09:00", "end": "18:00"},
                {"id": 2, "date": "2024-10-11", "start": "08:00", "end": "17:00"}
            ],
            "timeslots": [
                {"id": 1, "day_id": 1, "start": "11:00", "end": "12:00"},
                {"id": 3, "day_id": 2, "start": "09:30", "end": "16:00"}
            ]
        }
        mock_response = Mock()
        mock_response.json.return_value = mock_data
        mock_get.return_value = mock_response

        self.scheduler = Scheduler(url="https://example.com")

    def test_get_busy_slots(self):
        # Тест для даты с занятыми слотами
        result = self.scheduler.get_busy_slots("2024-10-10")
        self.assertEqual(result, [("11:00", "12:00")])

        # Тест для даты без занятых слотов
        result = self.scheduler.get_busy_slots("2024-10-12")
        self.assertEqual(result, [])

    def test_get_free_slots(self):
        # Тест для даты со свободными слотами
        result = self.scheduler.get_free_slots("2024-10-10")
        self.assertEqual(result, [("09:00", "11:00"), ("12:00", "18:00")])

        # Тест для даты с одним свободным слотом
        result = self.scheduler.get_free_slots("2024-10-11")
        self.assertEqual(result, [("08:00", "09:30"), ("16:00", "17:00")])

    def test_is_available(self):
        # Доступный слот
        self.assertTrue(self.scheduler.is_available("2024-10-10", "10:00", "10:30"))

        # Недоступный слот (пересекается с занятым)
        self.assertFalse(self.scheduler.is_available("2024-10-10", "11:30", "12:30"))

        # Слот вне рабочего времени
        self.assertFalse(self.scheduler.is_available("2024-10-10", "08:00", "09:00"))

    def test_find_slot_for_duration(self):
        # Поиск слота на 60 минут
        result = self.scheduler.find_slot_for_duration(60)
        self.assertEqual(result, ("2024-10-10", "09:00", "10:00"))

        # Поиск слота на 90 минут
        result = self.scheduler.find_slot_for_duration(90)
        self.assertEqual(result, ("2024-10-11", "08:00", "09:30"))

        # Поиск слота, который не может быть размещен
        result = self.scheduler.find_slot_for_duration(1000)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()