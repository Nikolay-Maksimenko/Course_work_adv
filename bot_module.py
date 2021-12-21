from random import randrange
from typing import Dict, ClassVar
from db_module import create_tables
import vk_api
from vk_api.upload import VkUpload
from vk_api.longpoll import VkLongPoll, VkEventType
import vk_module
import requests
from io import BytesIO
import settings
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

vk = vk_api.VkApi(token=settings.vkinder_token)
upload = VkUpload(vk)
longpoll = VkLongPoll(vk)
vk_token = settings.vk_token

def write_img(user_id: int, owner_id: int, photo_id: int, acces: str = '') -> None:
    """Отправка сообщения пользователю"""
    vk.method('messages.send', {'user_id': user_id, 'attachment': f'photo{owner_id}_{photo_id}_{acces}', 'random_id': randrange(10 ** 7)})

def write_msg(user_id: int, message: str, keyboard=None) -> None:
    """Отправка фотографии пользователю"""
    if keyboard != None:
        vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7), 'keyboard': keyboard.get_keyboard()})
    else:
        vk.method('messages.send', {'user_id': user_id, 'message': message, 'random_id': randrange(10 ** 7)})

def upload_img(upload, url):
    """Получение данных для отправки фотографии из внешних источников"""
    img = requests.get(url).content
    f = BytesIO(img)
    response = upload.photo_messages(f)[0]
    owner_id = response['owner_id']
    photo_id = response['id']
    access_key = response['access_key']
    return owner_id, photo_id, access_key

def input_age() -> int:
    """Обработка пользовательского ввода возраста"""
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

def input_relation() -> int:
    """Обработка пользовательского ввода семейного положения"""
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
            if event.to_me:
                request = event.text
                if request.lower() == 'д':
                    return True
                elif request.lower() == 'н':
                    return False
                else:
                    write_msg(event.user_id, 'Доступные команды: \n "Д" - Вы НЕ состоите в браке \n "Н" - Вы состоите в браке')
                    continue

def output_write_couple(couple: ClassVar, event_id, user_id, keyboard) -> None:
    """Отправка пользоаптелю ссылки на профиль и 3 фотографий с последующей записью этих данных в базу банных"""
    write_msg(event_id, couple.get_profile_link(), keyboard)
    for photo in couple.get_photo():
        write_img(event_id, couple.user_id, photo['id'])
    couple.write_couple_info(user_id)
    couple.write_photo_info()

def get_next_couple(person: Dict) -> ClassVar:
    couple = vk_module.VKUser(vk_token, next(person)['id'], '5.131')
    return couple

def create_buttons():
    keyboard = VkKeyboard()
    buttons = ['Далее', 'В избранное', 'В ЧС']
    colors = [VkKeyboardColor.PRIMARY, VkKeyboardColor.POSITIVE, VkKeyboardColor.NEGATIVE]
    for button, btn_color in zip(buttons, colors):
        keyboard.add_button(button, btn_color)
    keyboard.add_line()
    keyboard.add_button('Список избранных', VkKeyboardColor.POSITIVE)
    keyboard.add_button('Новый поиск', VkKeyboardColor.SECONDARY)
    return keyboard

def start_bot():
    """Основная логика бота"""
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
                if 'relation' in vk_user.information and vk_user.information['relation'] == 4:
                    write_msg(event.user_id, 'Вы состоите в браке!')
                    owner_id, photo_id, access_key = upload_img(upload, 'https://pbs.twimg.com/media/EQfUy3jXsAEpX6V.jpg')
                    write_img(event.user_id, owner_id, photo_id, access_key)
                    continue
                if 'relation' not in vk_user.information:
                    write_msg(event.user_id, 'Вы НЕ состоите в браке? (Д/Н)')
                    if input_relation():
                        vk_user.information['relation'] = 1
                    else:
                        write_msg(event.user_id, 'Бот не производит поиск для людей состоящих в браке!')
                        continue

                vk_user.write_user_info()
                person = vk_user.couple_generator()
                couple = get_next_couple(person)
                keyboard = create_buttons()
                create_buttons()
                output_write_couple(couple, event.user_id, vk_user.user_id, keyboard)
                for event in longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW:
                        if event.to_me:
                            request = event.text
                            if request.lower() == 'далее':
                                couple = get_next_couple(person)
                                output_write_couple(couple, event.user_id, vk_user.user_id, keyboard)
                            elif request.lower() == 'новый поиск':
                                write_msg(event.user_id, 'Введите Ваш ID')
                                break
                            elif request.lower() == 'в чс':
                                vk_user.write_black_list(couple.information['id'])
                                write_msg(event.user_id, 'Пользователь добавлен в черный список.')
                                continue
                            elif request.lower() == 'в избранное':
                                vk_user.write_white_list(couple)
                                write_msg(event.user_id, 'Пользователь добавлен в список избранных.')
                            elif request.lower() == 'список избранных':
                                if len(vk_user.get_favorite_list(vk_user.user_id)) != 0:
                                    write_msg(event.user_id, vk_user.get_favorite_list(vk_user.user_id))
                                else:
                                    write_msg(event.user_id, 'Список избранных пуст.')
                            else:
                                write_msg(event.user_id, 'Такая команда отсутствует!')
