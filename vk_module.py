import vk_api
import datetime
from typing import List, Tuple, Dict, Optional, Generator
from db_module import engine, session, create_engine, VKinderUser, DatingUser, Photos

class VKUser:
    def __init__(self, token: str, user_id: str, api_version: str):
        self.token = token
        self.user_id = user_id
        self.api_version = api_version
        self.information = self.get_information()
        self.user_id = self.get_user_id()
        self.age = self.get_age()

    def get_information(self) -> Dict:
        vk = vk_api.VkApi(token=self.token)
        information = vk.method('users.get', {'user_ids': self.user_id, 'fields': 'bdate, city, sex, relation'})
        return information[0]

    def get_user_id(self) -> int:
        user_id = self.information['id']
        return user_id

    def get_age(self) -> int:
        if 'bdate' not in self.information:
            return None
        try:
            day, month, year = map(int, self.information['bdate'].split('.'))
        except (ValueError, AttributeError):
            return None
        age = int((datetime.date.today() - datetime.date(year, month, day)).days / 365)
        return age

    def get_search_params(self) -> Dict:
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
        vk = vk_api.VkApi(token=self.token)
        params = self.get_search_params()
        candidates_list = vk.method('users.search',
            {'sort': 0, 'count': 1000, 'city': params['city'], 'sex': params['gender'], 'status': [1, 6],
             'age_from': params['age_from'], 'age_to': params['age_to'],'has_photo': 1, 'fields': 'relation'})
        return candidates_list

    def couple_generator(self) -> Dict:
        for persona in self.search_couple()['items']:
            if self.check_ids(persona['id']) == False and persona['is_closed'] == False and 'relation' in persona:
                if persona['relation'] in (1,6):
                    yield persona
                else:
                    continue

    def write_user_info(self) -> None:
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
        ids_in_base = session.query(DatingUser.vk_id, DatingUser.user_id).all()
        status = (couple_id, self.user_id) in ids_in_base
        return status

    def write_couple_info(self, vkinder_user_id: int) -> None:
        write_data = (self.information['id'], self.information['first_name'], self.information['last_name'], self.information['bdate'], vkinder_user_id)
        table_columns = list(filter(lambda x: not x.startswith('_') and x != 'id', DatingUser.__dict__))
        write_dict = dict(zip(table_columns, write_data))
        add_record = DatingUser(**write_dict)
        session.add(add_record)
        session.commit()

    def write_photo_info(self) -> None:
        photos_inf = self.get_photo()
        write_data_list = [(self.information['id'], photo['id'], photo['url']) for photo in photos_inf]
        table_columns = list(filter(lambda x: not x.startswith('_') and x != 'id', Photos.__dict__))
        for write_data in write_data_list:
            write_dict = dict(zip(table_columns, write_data))
            add_record = Photos(**write_dict)
            session.add(add_record)
        session.commit()

    def get_photo(self, number: int = 3) -> List[Dict]:
        vk = vk_api.VkApi(token=self.token)
        result = vk.method('photos.get', {'owner_id': self.user_id, 'album_id': 'profile', 'count': 1000, 'extended': 1, 'photo_sizes': 1})['items']
        photos = [(i['likes']['count'] + i['comments']['count'], i['id'] ,i['sizes'][-1]['url']) for i in result]
        photos = sorted(photos, reverse=True)
        photos_inf = [{'id': i[1], 'url': i[2]} for i in photos[:number]]
        return photos_inf

    def get_profile_link(self) -> str:
        link = f'https://vk.com/id{self.user_id}'
        return link
