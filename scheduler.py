import requests
from datetime import datetime, timedelta


class Scheduler:
    def __init__(self, url):
        """Инициализация планировщика с URL API.
        Args:
            url (str): URL endpoint для получения данных о расписании
        """
        self.url = url
        self.data = self._fetch_data()  # Загружаем данные при инициализации
        # Преобразуем дни в словарь {дата: день} для быстрого доступа
        self.days = {day['date']: day for day in self.data['days']}
        # Организуем таймслоты по датам
        self.timeslots = self._organize_timeslots()

    def _fetch_data(self):
        """Получение данных о расписании с API.
        Returns:
            dict: Данные о рабочих днях и занятых слотах
        Raises:
            HTTPError: Если запрос к API не удался
        """
        response = requests.get(self.url)
        response.raise_for_status()  # Проверяем на ошибки HTTP
        return response.json()

    def _organize_timeslots(self):
        """Группирует таймслоты по датам для удобного доступа.
        Returns:
            dict: Словарь {дата: список таймслотов}
        """
        timeslots_by_date = {}
        # Инициализируем пустые списки для каждой даты
        for day in self.data['days']:
            date = day['date']
            timeslots_by_date[date] = []

        # Распределяем таймслоты по соответствующим датам
        for timeslot in self.data['timeslots']:
            day_id = timeslot['day_id']
            # Находим дату по day_id
            date = next((day['date'] for day in self.data['days'] if day['id'] == day_id), None)
            if date:
                timeslots_by_date[date].append((timeslot['start'], timeslot['end']))

        return timeslots_by_date

    def _time_to_minutes(self, time_str):
        """Конвертирует время в формате 'ЧЧ:ММ' в минуты с начала дня.
        Args:
            time_str (str): Время в формате 'ЧЧ:ММ'
        Returns:
            int: Количество минут с начала дня
        """
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes

    def _minutes_to_time(self, minutes):
        """Конвертирует минуты с начала дня в формат 'ЧЧ:ММ'.
        Args:
            minutes (int): Количество минут с начала дня
        Returns:
            str: Время в формате 'ЧЧ:ММ'
        """
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"

    def _parse_time_range(self, start, end):
        """Парсит временной диапазон в минуты.
        Args:
            start (str): Начальное время 'ЧЧ:ММ'
            end (str): Конечное время 'ЧЧ:ММ'
        Returns:
            tuple: (начало в минутах, конец в минутах)
        """
        return self._time_to_minutes(start), self._time_to_minutes(end)

    def _merge_overlapping_slots(self, slots):
        """Объединяет пересекающиеся временные интервалы.
        Args:
            slots (list): Список интервалов в формате [(start, end), ...]
        Returns:
            list: Список объединенных интервалов
        """
        if not slots:
            return []

        # Сортируем интервалы по времени начала
        sorted_slots = sorted(slots, key=lambda x: x[0])
        merged = [sorted_slots[0]]

        # Объединяем пересекающиеся интервалы
        for current in sorted_slots[1:]:
            last = merged[-1]
            if current[0] <= last[1]:  # Если интервалы пересекаются
                merged[-1] = (last[0], max(last[1], current[1]))  # Объединяем
            else:
                merged.append(current)  # Добавляем новый интервал

        return merged

    def get_busy_slots(self, date):
        """Возвращает занятые промежутки времени для указанной даты.
        Args:
            date (str): Дата в формате 'ГГГГ-ММ-ДД'
        Returns:
            list: Список кортежей (начало, конец) занятых промежутков
        """
        if date not in self.timeslots:
            return []

        busy_slots = self.timeslots[date]
        return self._merge_overlapping_slots(busy_slots)

    def get_free_slots(self, date):
        """Возвращает свободные промежутки времени для указанной даты.
        Args:
            date (str): Дата в формате 'ГГГГ-ММ-ДД'
        Returns:
            list: Список кортежей (начало, конец) свободных промежутков
        """
        if date not in self.days:
            return []

        work_day = self.days[date]
        work_start, work_end = self._parse_time_range(work_day['start'], work_day['end'])
        busy_slots = self.get_busy_slots(date)

        free_slots = []
        prev_end = work_start  # Отслеживаем конец последнего занятого/рабочего периода

        for busy_start, busy_end in busy_slots:
            busy_start_min, busy_end_min = self._parse_time_range(busy_start, busy_end)
            if busy_start_min > prev_end:
                # Добавляем свободный промежуток между предыдущим концом и началом занятого
                free_slots.append((
                    self._minutes_to_time(prev_end),
                    self._minutes_to_time(busy_start_min)
                ))
            prev_end = max(prev_end, busy_end_min)

        # Добавляем оставшийся свободный промежуток в конце дня
        if prev_end < work_end:
            free_slots.append((
                self._minutes_to_time(prev_end),
                self._minutes_to_time(work_end)
            ))

        return free_slots

    def is_available(self, date, start, end):
        """Проверяет доступность временного промежутка.
        Args:
            date (str): Дата в формате 'ГГГГ-ММ-ДД'
            start (str): Начало промежутка 'ЧЧ:ММ'
            end (str): Конец промежутка 'ЧЧ:ММ'
        Returns:
            bool: Доступен ли промежуток
        """
        if date not in self.days:
            return False

        work_day = self.days[date]
        work_start, work_end = self._parse_time_range(work_day['start'], work_day['end'])
        slot_start, slot_end = self._parse_time_range(start, end)

        # Проверяем, что слот в пределах рабочего дня
        if slot_start < work_start or slot_end > work_end:
            return False

        busy_slots = self.get_busy_slots(date)

        # Проверяем пересечение с занятыми слотами
        for busy_start, busy_end in busy_slots:
            busy_start_min, busy_end_min = self._parse_time_range(busy_start, busy_end)
            if not (slot_end <= busy_start_min or slot_start >= busy_end_min):
                return False

        return True

    def find_slot_for_duration(self, duration_minutes):
        """Находит первый подходящий свободный слот для указанной продолжительности.
        Args:
            duration_minutes (int): Продолжительность в минутах
        Returns:
            tuple: (дата, начало, конец) или None, если слот не найден
        """
        # Проверяем дни в хронологическом порядке
        for date in sorted(self.days.keys()):
            free_slots = self.get_free_slots(date)
            for start, end in free_slots:
                start_min = self._time_to_minutes(start)
                end_min = self._time_to_minutes(end)
                available_duration = end_min - start_min
                if available_duration >= duration_minutes:
                    return (date, start, self._minutes_to_time(start_min + duration_minutes))

        return None