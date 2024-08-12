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

class Joomla3Launcher(WebAppLauncher):

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
        except Exception as e:
            print(e)
            traceback.print_exc()

    def prepare_files(self):
        destFile = self.configuration['web_app_sources']

        with open(os.path.join(destFile, '.htaccess'), 'w') as f:
            f.write('php_flag magic_quotes_gpc Off\n')

        subprocess.call(['chmod', '-R', '777', 'staged_webapp'])

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

            url = 'http://localhost:8080/installation/index.php'
            data = {
                "format": "json",
                "jform[site_name]": "Test",
                "jform[site_metadesc]": "",
                "jform[admin_email]": "test@test.com",
                "jform[admin_user]": "test",
                "jform[admin_password]": "password",
                "jform[admin_password2]": "password",
                "jform[site_offline]": "0",
                "task": "setup.site",
                token: "1"
            }
            response = s.post(url, data=data, headers=headers)
            token = response.json()['token']

            # Step 2
            url = 'http://localhost:8080/installation/index.php'
            data = {
                "format": "json",
                "jform[db_type]": "mysqli",
                "jform[db_host]": "mysql",
                "jform[db_user]": "joomla",
                "jform[db_pass]": "password",
                "jform[db_name]": "joomla",
                "jform[db_prefix]": "joomla_",
                "jform[db_old]": "backup",
                "task": "setup.database",
                token: "1"
            }
            response = s.post(url, data=data, headers=headers)
            token = response.json()['token']

            # # Step 3: Get the current page and make the verification file
            # verificationFile = response.json()['messages']['error'][0].split('&quot;')[1]
            # with open(os.path.join(self.configuration['web_app_sources'], 'installation', verificationFile), 'w') as f:
            #     f.write('')
            # token = response.json()['token']

            # # Step 4
            # url = 'http://localhost:8080/installation/index.php'
            # data = {
            #     "format: json": "",
            #     "jform[db_type]": "mysqli",
            #     "jform[db_host]": "mysql",
            #     "jform[db_user]": "joomla",
            #     "jform[db_pass]": "password",
            #     "jform[db_name]": "joomla",
            #     "jform[db_prefix]": "joomla_",
            #     "jform[db_old]": "backup",
            #     "task": "database",
            #     token: "1"
            # }
            # response = s.post(url, data=data, headers=headers)
            # token = response.json()['token']

            # url = 'http://localhost:8080/installation/index.php?tmpl=body&view=summary'
            # response = s.get(url, headers=headers)

            # Step 5
            url = 'http://localhost:8080/installation/index.php'
            data = {
                "format": "json",
                "jform[sample_file]": "",
                "jform[summary_email]": "0",
                "jform[summary_email_passwords]": "0",
                "task": "setup.summary",
                token: "1"
            }
            response = s.post(url, data=data, headers=headers)
            token = response.json()['token']


            # Step 6
            url = 'http://localhost:8080/installation/index.php?task=setup.install_database_backup'
            data = {
                "format": "json",
                token: "1"
            }
            response = s.post(url, data=data, headers=headers)
            token = response.json()['token']


            # Step 7
            url = 'http://localhost:8080/installation/index.php?task=setup.install_database'
            data = {
                "format": "json",
                token: "1"
            }
            response = s.post(url, data=data, headers=headers)
            token = response.json()['token']

            # Step 8
            url = 'http://localhost:8080/installation/index.php?task=setup.install_config'
            data = {
                "format": "json",
                token: "1"
            }
            response = s.post(url, data=data, headers=headers)
            token = response.json()['token']

            # url = 'http://localhost:8080/installation/index.php?tmpl=body&view=complete'
            # response = s.get(url, headers=headers)

            # Step 9
            # shutil.rmtree(os.path.join(self.configuration['web_app_sources'], 'installation'))
            url = 'http://localhost:8080/installation/index.php?task=setup.removeFolder'
            data = {
                "format": "json",
                "instDefault" : "Remove installation folder",
                token: "1"
            }
            response = s.post(url, data=data, headers=headers)

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
            response = s.get('http://localhost:8080/administrator/index.php?option=com_admin&view=sysinfo')
            versionCheck = re.compile(self.configuration['version_check']['regex'])
            return versionCheck.findall(response.content.decode('utf-8'))
