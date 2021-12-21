import vk_api
import datetime
from typing import List, Dict, Generator, ClassVar
from db_module import  session, VKinderUser, DatingUser, Photos, BlackList,  WhiteList

class VKUser:
    def __init__(self, token: str, user_id: str, api_version: str):
        self.token = token
        self.user_id = user_id
        self.api_version = api_version
        self.information = self.get_information()
        self.user_id = self.get_user_id()
        self.age = self.get_age()

    def get_information(self) -> Dict:
        """Получение данных пользователя по его id (Имя, Фамилия, пол, дата рождения, город, семейное положение, скрыт ли профиль"""
        vk = vk_api.VkApi(token=self.token)
        information = vk.method('users.get', {'user_ids': self.user_id, 'fields': 'bdate, city, sex, relation'})
        return information[0]

    def get_user_id(self) -> int:
        """Получение id пользователя по его короткому имени"""
        user_id = self.information['id']
        return user_id

    def get_age(self) -> int:
        """Вычисляет возраст пользователя"""
        if 'bdate' not in self.information:
            return None
        try:
            day, month, year = map(int, self.information['bdate'].split('.'))
        except (ValueError, AttributeError):
            return None
        age = int((datetime.date.today() - datetime.date(year, month, day)).days / 365)
        return age

    def get_search_params(self) -> Generator:
        """Формирует словарь с параметрами для поиска пар на основании данных о пользователе бота"""
        age_from = self.age - 5
        if age_from < 18:
            age_from = 18
        age_to = self.age + 5
        city = self.information.get('city')['id']
        own_gender = self.information.get('sex')
        if own_gender == 1:
            gender = 2
        else:
            gender = 1
        relation = self.information.get('relation')
        params = {'age_from': age_from, 'age_to': age_to, 'city': city, 'gender': gender, 'relation': relation}
        return params

    def search_couple(self) -> List[List]:
        """Формирует список потенциальных пар"""
        vk = vk_api.VkApi(token=self.token)
        params = self.get_search_params()
        candidates_list = vk.method('users.search',
            {'sort': 0, 'count': 1000, 'city': params['city'], 'sex': params['gender'], 'status': [1, 6],
             'age_from': params['age_from'], 'age_to': params['age_to'],'has_photo': 1, 'fields': 'relation'})
        return candidates_list

    def couple_generator(self) -> Dict:
        """Генератор пар. Возвращает только открытые аккаунты у которых в семейном положении указаны следующие значения: свободен(на)/в активном поиске"""
        for persona in self.search_couple()['items']:
            if self.check_ids(persona['id']) == True and persona['is_closed'] == False and 'relation' in persona:
                if persona['relation'] in (1,6):
                    yield persona
                else:
                    continue

    def write_user_info(self) -> None:
        """Записывает в базу данных информацию о пользователе бота (таблица vkinder_user)"""
        vkid_in_base = [vk_id[0] for vk_id in session.query(VKinderUser.vk_id).all()]
        if  self.user_id not in vkid_in_base:
            write_data = (self.information['id'], self.information['first_name'], self.information['last_name'],
                          self.age, self.information['city']['id'], self.information['city']['title'])
            table_columns = list(filter(lambda x: not x.startswith('_') and x != 'id', VKinderUser.__dict__))
            write_dict = dict(zip(table_columns, write_data))
            add_record = VKinderUser(**write_dict)
            session.add(add_record)
            session.commit()

    def check_ids(self, couple_id: int) -> bool:
        """Проверяет наличие информации о человеке в базе данных (таблицы dating_user и black_list)"""
        ids_dating_user = session.query(DatingUser.vk_id, DatingUser.user_id).all()
        ids_blacklist = session.query(BlackList.vkinder_id, BlackList.couple_id).all()
        status = (couple_id, self.user_id) not in ids_dating_user and (self.user_id, couple_id) not in ids_blacklist
        return status

    def write_to_database(self, data: tuple, table) -> None:
        table_columns = list(filter(lambda x: not x.startswith('_') and x != 'id', table.__dict__))
        write_dict = dict(zip(table_columns, data))
        add_record = table(**write_dict)
        session.add(add_record)
        session.commit()

    def write_couple_info(self, vkinder_user_id: int) -> None:
        """Записывает в базу данных информацию о человеке (таблица dating_user)"""
        write_data = (self.information['id'], self.information['first_name'], self.information['last_name'], self.information['bdate'], vkinder_user_id)
        self.write_to_database(write_data, DatingUser)

    def write_photo_info(self) -> None:
        """Записывает в базу данных информацию о фотографиях (таблица photos)"""
        photos_inf = self.get_photo()
        write_data_list = [(self.information['id'], photo['id'], photo['url']) for photo in photos_inf]
        table_columns = list(filter(lambda x: not x.startswith('_') and x != 'id', Photos.__dict__))
        for write_data in write_data_list:
            write_dict = dict(zip(table_columns, write_data))
            add_record = Photos(**write_dict)
            session.add(add_record)
        session.commit()

    def write_black_list(self, couple_id: int) -> bool:
        """Записывает в базу данных id человека добавленного в черный список (таблица black_list)"""
        write_data = (self.information['id'], couple_id)
        if write_data not in session.query(BlackList.vkinder_id, BlackList.couple_id).all():
            self.write_to_database(write_data, BlackList)

    def write_white_list(self, couple: ClassVar) -> None:
        write_data = (self.information['id'], couple.information['id'], couple.information['first_name'], couple.information['last_name'], couple.get_profile_link())
        if write_data not in session.query(WhiteList.vkinder_id, WhiteList.couple_id, WhiteList.first_name, WhiteList.last_name, WhiteList.url).all():
            self.write_to_database(write_data, WhiteList)

    def get_favorite_list(self, user_id):
        favorite_users = session.query(WhiteList.first_name, WhiteList.last_name, WhiteList.url).filter_by(vkinder_id=user_id).all()
        favorite_users = [' '.join(user) for user in favorite_users]
        favorite_users = '\n'.join(favorite_users)
        return favorite_users

    def get_photo(self, number: int = 3) -> List[Dict]:
        """Возвращает список данных о самых популярных фотографиях пользователя (по умолчанию 3шт)"""
        vk = vk_api.VkApi(token=self.token)
        result = vk.method('photos.get', {'owner_id': self.user_id, 'album_id': 'profile', 'count': 1000, 'extended': 1, 'photo_sizes': 1})['items']
        photos = [(i['likes']['count'] + i['comments']['count'], i['id'] ,i['sizes'][-1]['url']) for i in result]
        photos = sorted(photos, reverse=True)
        photos_inf = [{'id': i[1], 'url': i[2]} for i in photos[:number]]
        return photos_inf

    def get_profile_link(self) -> str:
        """Формирует ссылку на аккаунт пользователя ВК"""
        link = f'https://vk.com/id{self.user_id}'
        return link