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
import traceback

class Joomla4_2Launcher(WebAppLauncher):

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
        try:
            return self.setup_joomla()
        except:
            traceback.print_exc()

    def prepare_files(self):
        destFile = self.configuration['web_app_sources']
        os.chmod(destFile, 0o777)
        os.chmod(os.path.join(destFile, "administrator/cache"), 0o777)
        os.chmod(os.path.join(destFile, "installation"), 0o777)

    def setup_joomla(self):
        with requests.Session() as s:
            headers = { 'Cookie' : 'wordpress_test_cookie=WP Cookie check' }
            headers = {}

            # Step 1
            url = 'http://localhost:8080/installation/index.php'
            response = s.get(url, headers=headers)
            soup = BeautifulSoup(response.content.decode('utf-8'), features="html.parser")
            try:
                token = soup.findAll('input', attrs={'type' : 'hidden', 'value' : '1'})[0].attrs['name']
            except Exception as e:
                token = ''

            url = 'http://localhost:8080/installation/index.php?task=installation.dbcheck&format=json'
            data = {
                "jform[site_name]": "Test",
                "jform[admin_user]": "test",
                "jform[admin_username]": "test",
                "jform[admin_password]": "password!@#$%",
                "jform[admin_email]": "test@test.com",
                "jform[db_type]": "mysqli",
                "jform[db_host]": "mysql",
                "jform[db_user]": "joomla",
                "jform[db_pass]": "password",
                "jform[db_name]": "joomla",
                "jform[db_prefix]": "joomla_",
                "jform[db_encryption]": "0",
                "jform[db_sslkey]": "",
                "jform[db_sslcert]": "",
                "jform[db_sslverifyservercert]": "0",
                "jform[db_sslca]": "",
                "jform[db_sslcipher]": "",
                "jform[db_old]": "backup",
                "admin_password2": "password!@#$%",
                token: "1"
            }
            response = s.post(url, data=data, headers=headers)
            fileName = response.json()['messages']['notice'][0]
            verificationFile = fileName.split(' ')[15][1:-1]
            os.remove(os.path.join(self.configuration["web_app_sources"], "installation", verificationFile))
            # with open(os.path.join(self.configuration['web_app_sources'], 'installation', verificationFile), 'w') as f:
            #     f.write('')

            # Step 2 - submit the same stuff again
            data[response.json()['token']] = "1"
            response = s.post(url, data=data, headers=headers)

            data[response.json()['token']] = "1"
            response = s.post('http://localhost:8080/installation/index.php?task=installation.create&format=json', data=data, headers=headers)

            data[response.json()['token']] = "1"
            response = s.post('http://localhost:8080/installation/index.php?task=installation.populate1&format=json', data=data, headers=headers)

            data[response.json()['token']] = "1"
            response = s.post('http://localhost:8080/installation/index.php?task=installation.populate2&format=json', data=data, headers=headers)

            data[response.json()['token']] = "1"
            response = s.post('http://localhost:8080/installation/index.php?task=installation.populate3&format=json', data=data, headers=headers)

            data[response.json()['token']] = "1"
            response = s.post('http://localhost:8080/installation/index.php?task=installation.custom1&format=json', data=data, headers=headers)

            data[response.json()['token']] = "1"
            response = s.post('http://localhost:8080/installation/index.php?task=installation.custom2&format=json', data=data, headers=headers)

            data[response.json()['token']] = "1"
            response = s.post('http://localhost:8080/installation/index.php?task=installation.config&format=json', data=data, headers=headers)

            # Step 9
            shutil.rmtree(os.path.join(self.configuration['web_app_sources'], 'installation'))

            # # data['token'] = response.json()['token']
            # response = s.post('http://localhost:8080/installation/index.php?task=installation.removeFolder&format=json', headers=headers)

            # Step 10: Login to admin panel
            url = 'http://localhost:8080/administrator'
            response = s.get(url=url, headers=headers)
            soup = BeautifulSoup(response.content.decode('utf-8'), features="html.parser")
            try:
                token = soup.findAll('input', attrs={'type' : 'hidden', 'value' : '1'})[0].attrs['name']
            except:
                token = ''

            data = {
                "username": "test",
                "passwd": "password!@#$%",
                "option": "com_login",
                "task": "login",
                "return": "aW5kZXgucGhw",
                token: "1"
            }
            response = s.post('http://localhost:8080/administrator/index.php', data=data, headers=headers)

            # Step 8: Get the homepage to get the version number
            response = s.get('http://localhost:8080/administrator/index.php')
            versionCheck = re.compile(self.configuration['version_check']['regex'])
            return versionCheck.findall(response.content.decode('utf-8'))
