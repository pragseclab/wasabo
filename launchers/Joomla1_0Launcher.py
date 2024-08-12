from .WebAppLauncher import WebAppLauncher
from bs4 import BeautifulSoup
import fileinput
import subprocess
import requests
import time
import re
import os
import shutil
import stat

class Joomla1_0Launcher(WebAppLauncher):

    def __init__(self, configuration):
        super().__init__(configuration)
        self.containers = []

    def launch(self):
        # Set the volume location to that of the wordpress source location
        self.configuration['docker']['php']['volumes'] = {os.path.abspath(self.configuration['web_app_sources']) : {'bind' : '/var/www/html/',
                                                                                                                    'mode' : 'rw'}}
        # Create the containers
        self.network = self.docker.create_network('wordpress')
        self.containers = self.launch_docker_containers(self.configuration['docker'])

        # Wait for MySQL container to accept connections before attempting to install Wordpress
        mysql_container = [container for container in self.containers if 'mysql' in container.name][0]
        self.wait_for_mysql(mysql_container)

        self.prepare_files()
        return self.setup_joomla()

    def prepare_files(self):
        destFile = self.configuration['web_app_sources']
        # os.chmod(destFile, 0o777)
        subprocess.call(['chmod', '-R', '777', 'staged_webapp'])

    def get_token(self, response):
        soup = BeautifulSoup(response.content.decode('utf-8'), features="html.parser")
        try:
            token = soup.findAll('input', attrs={'type' : 'hidden', 'value' : '1'})[0].attrs['name']
        except Exception as e:
            token = ''

        return token

    def setup_joomla(self):
        with requests.Session() as s:
            headers = { 'Cookie' : 'wordpress_test_cookie=WP Cookie check' }
            headers = {}

            # Step 1
            url = 'http://localhost:8080/installation/install1.php'
            data = {
	        "next": "Next+>>"
            }
            response = s.post(url, data=data, headers=headers)

            url = 'http://localhost:8080/installation/install2.php'
            data = {
                "next": "Next+>>",
                "DBhostname": "mysql",
                "DBuserName": "joomla",
                "DBpassword": "password",
                "DBname": "joomla",
                "DBPrefix": "joomla_"
            }
            response = s.post(url, data=data, headers=headers)

            # Step 2
            url = 'http://localhost:8080/installation/install3.php'
            data = {
                "DBhostname": "mysql",
                "DBuserName": "joomla",
                "DBpassword": "password",
                "DBname": "joomla",
                "DBPrefix": "joomla_",
                "DBcreated": "1",
                "next": "Next+>>",
                "sitename": "Test"
            }
            response = s.post(url, data=data, headers=headers)

            # Step 5
            url = 'http://localhost:8080/installation/install4.php'
            data = {
                "DBhostname": "mysql",
                "DBuserName": "joomla",
                "DBpassword": "password",
                "DBname": "joomla",
                "DBPrefix": "joomla_",
                "sitename": "Test",
                "next": "Next+>>",
                "siteUrl": "http://localhost:8080",
                "absolutePath": "/var/www/html",
                "adminEmail": "test@test.com",
                "adminPassword": "password",
                "filePermsMode": "0",
                "filePermsUserRead": "1",
                "filePermsUserWrite": "1",
                "filePermsGroupRead": "1",
                "filePermsWorldRead": "1",
                "dirPermsMode": "0",
                "dirPermsUserRead": "1",
                "dirPermsUserWrite": "1",
                "dirPermsUserSearch": "1",
                "dirPermsGroupRead": "1",
                "dirPermsGroupSearch": "1",
                "dirPermsWorldRead": "1",
                "dirPermsWorldSearch": "1"
            }
            response = s.post(url, data=data, headers=headers)

            # Step 9
            shutil.rmtree(os.path.join(self.configuration['web_app_sources'], 'installation'))

            # Step 10: Login to admin panel
            url = 'http://localhost:8080/administrator/index.php'
            data = {
                "usrname": "admin",
                "pass": "password",
                "submit": "Login"
            }
            response = s.post(url, data=data, headers=headers)

            # Step 8: Get the homepage to get the version number
            response = s.get('http://localhost:8080/administrator/index2.php')
            versionCheck = re.compile(self.configuration['version_check']['regex'])
            return versionCheck.findall(response.content.decode('utf-8'))
