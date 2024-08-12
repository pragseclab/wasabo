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

class Joomla1_6Launcher(WebAppLauncher):

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
            url = 'http://localhost:8080/installation/index.php'
            response = s.get(url, headers=headers)
            response = s.get(url, headers=headers)
            token = self.get_token(response)

            url = 'http://localhost:8080/installation/index.php'
            data = {
                "jform[language]": "en-US",
                "task": "setup.setlanguage",
                token: "1"
            }
            response = s.post(url, data=data, headers=headers)
            token = self.get_token(response)

            # Step 2
            url = 'http://localhost:8080/installation/index.php'
            data = {
                "jform[db_type]": "mysqli",
                "jform[db_host]": "mysql",
                "jform[db_user]": "joomla",
                "jform[db_pass]": "password",
                "jform[db_name]": "joomla",
                "jform[db_prefix]": "joomla_",
                "jform[db_old]": "backup",
                "task": "setup.database",
                token: "1",
            }
            response = s.post(url, data=data, headers=headers)
            token = self.get_token(response)

            # Step 5
            url = 'http://localhost:8080/installation/index.php'
            data = {
                "jform[ftp_enable]": "0",
                "jform[ftp_user]": "",
                "jform[ftp_pass]": "",
                "jform[ftp_root]": "",
                "jform[ftp_host]": "127.0.0.1",
                "jform[ftp_port]": "21",
                "jform[ftp_save]": "0",
                "task": "setup.filesystem",
                token: "1",
            }
            response = s.post(url, data=data, headers=headers)
            token = self.get_token(response)

            # Step 6
            url = 'http://localhost:8080/installation/index.php'
            data = {
                "jform[site_name]": "Test",
                "jform[site_metadesc]": "",
                "jform[site_metakeys]": "",
                "jform[site_offline]": "0",
                "jform[admin_email]": "test@test.com",
                "jform[admin_user]": "test",
                "jform[admin_password]": "password",
                "jform[admin_password2]": "password",
                "task": "setup.saveconfig",
                token: "1",
                "jform[sample_installed]": "0",
            }
            response = s.post(url, data=data, headers=headers)
            token = self.get_token(response)

            # Step 9
            shutil.rmtree(os.path.join(self.configuration['web_app_sources'], 'installation'))

            # Step 10: Login to admin panel
            url = 'http://localhost:8080/administrator/index.php'
            response = s.get(url=url, headers=headers)
            soup = BeautifulSoup(response.content.decode('utf-8'), features="html.parser")
            try:
                token = soup.findAll('input', attrs={'type' : 'hidden', 'value' : '1'})[0].attrs['name']
            except:
                token = ''

            data = {
                "username": "test",
                "passwd": "password",
                "option": "com_login",
                "task": "login",
                "return": "aW5kZXgucGhw",
                token: "1"
            }
            response = s.post(url, data=data, headers=headers)

            # Step 8: Get the homepage to get the version number
            response = s.get('http://localhost:8080/administrator/index.php')
            versionCheck = re.compile(self.configuration['version_check']['regex'])
            return versionCheck.findall(response.content.decode('utf-8'))