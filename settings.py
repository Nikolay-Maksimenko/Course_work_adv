import os
vkinder_token = os.getenv('VKINDER_API_KEY')
vk_token = os.getenv('VKUSER_API_KEY')
db_setting = f'postgresql://{os.getenv("BD_USER")}:{os.getenv("BD_PWD")}@localhost:5432/vkinder'