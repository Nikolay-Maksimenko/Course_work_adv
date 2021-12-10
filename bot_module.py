from random import randrange
from typing import Dict
from db_module import create_tables
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import vk_module
import os


def write_img(user_id: int, owner_id: int, photo_id: int) -> None:
    vk.method('messages.send', {'user_id': user_id, 'attachment': f'photo{owner_id}_{photo_id}', 'random_id': randrange(10 ** 7)})

def write_msg(user_id: int, message: str) -> None:
    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7),})

def input_age() -> int:
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text
                if request.isdigit() and 18 < int(request) < 100:
                    age = int(request)
                    return age
                else:
                    write_msg(event.user_id, 'Допустимые значения возраста в диапазоне 18-100 лет')
                    continue

def output_write_couple(person: Dict) -> None:
    couple = vk_module.VKUser(vk_token, next(person)['id'], '5.131')
    write_msg(event.user_id, couple.get_profile_link())
    for photo in couple.get_photo():
        write_img(event.user_id, couple.user_id, photo['id'])
    couple.write_couple_info(vk_user.user_id)
    couple.write_photo_info()

if __name__ == '__main__':
    vkinder_token = os.getenv('VKINDER_API_KEY')
    vk = vk_api.VkApi(token=vkinder_token)
    longpoll = VkLongPoll(vk)
    vk_token = os.getenv('VKUSER_API_KEY')
    create_tables()

    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text
                try:
                    vk_user = vk_module.VKUser(vk_token, request, '5.131')
                except vk_api.exceptions.ApiError:
                    write_msg(event.user_id, 'Введите Ваш ID!')
                    continue
                if vk_user.age == None:
                    write_msg(event.user_id, 'Введите Ваш возраст')
                    vk_user.age = input_age()
                if 'city' not in vk_user.information:
                    write_msg(event.user_id, 'Пожалуйста, укажите свой город в настройках аккаунта.\n https://vk.com/edit?act=contacts')
                    continue
                vk_user.write_user_info()
                person = vk_user.couple_generator()
                output_write_couple(person)
                for event in longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW:
                        if event.to_me:
                            request = event.text
                            if request.lower() in ("next", "далее"):
                                output_write_couple(person)
                            elif request.lower() in ("exit", "выход"):
                                break
                            else:
                                write_msg(event.user_id, 'Такая команда отсутствует! \n "далее"/"next" - следующий человек \n "выход"/"exit" - начать новый поиск')
