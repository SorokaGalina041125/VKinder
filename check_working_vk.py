# import os
# import requests
# from dotenv import load_dotenv
#
#
# load_dotenv()
#
# class VK:
#     def __init__(self, access_token=None, user_id=None, version='5.199'):
#         self.token = access_token or os.getenv('VK_GROUP_TOKEN')
#         self.id = user_id or os.getenv('VK_USER_ID')
#         self.version = version
#         self.params = {'access_token': self.token, 'v': self.version}
#
#     def users_info(self):
#         url = 'https://api.vk.com/method/users.get'
#         params = {'user_ids': self.id}
#         response = requests.get(url, params={**self.params, **params})
#         self.id = response.json()['response'][0]['id']
#         self.user_name = response.json()['response'][0]['first_name'] + ' ' + response.json()['response'][0]['last_name']
#         self.user_photo =
#
#
#
#
#
# vk = VK()
#
#
# print(vk.users_info())
#


