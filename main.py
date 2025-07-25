from scheduler import Scheduler

# Тестовые данные
test_data = {
    "days": [
        {"id": 1, "date": "2024-10-10", "start": "09:00", "end": "18:00"},
        {"id": 2, "date": "2024-10-11", "start": "08:00", "end": "17:00"}
    ],
    "timeslots": [
        {"id": 1, "day_id": 1, "start": "11:00", "end": "12:00"},
        {"id": 3, "day_id": 2, "start": "09:30", "end": "16:00"}
    ]
}

# Тестовый класс, переопределяющий загрузку данных
class TestScheduler(Scheduler):
    def _fetch_data(self):
        """Переопределяем метод загрузки для использования тестовых данных."""
        return test_data

# Создаем экземпляр тестового планировщика
scheduler = TestScheduler(url="https://example.com")

# Демонстрация работы методов
print("=== Занятые промежутки 2024-10-10 ===")
print(scheduler.get_busy_slots("2024-10-10"))  # Ожидаем [('11:00', '12:00')]

print("\n=== Свободные промежутки 2024-10-10 ===")
print(scheduler.get_free_slots("2024-10-10"))  # Ожидаем [('09:00', '11:00'), ('12:00', '18:00')]

print("\n=== Проверка доступности ===")
print("10:00-10:30:", scheduler.is_available("2024-10-10", "10:00", "10:30"))  # True
print("11:30-12:30:", scheduler.is_available("2024-10-10", "11:30", "12:30"))  # False

print("\n=== Поиск слота для продолжительности ===")
print("60 минут:", scheduler.find_slot_for_duration(60))  # ('2024-10-10', '09:00', '10:00')
print("90 минут:", scheduler.find_slot_for_duration(90))  # ('2024-10-11', '08:00', '09:30')