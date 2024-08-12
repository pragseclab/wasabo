from .WebAppLauncher import WebAppLauncher
from bs4 import BeautifulSoup
import fileinput
import requests
import time
import re
import os
import shutil
import stat

class MediaWikiLauncher(WebAppLauncher):

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

        # self.prepare_files()
        return self.setup_drupal()

    def prepare_files(self):
        php_container = [container for container in self.containers if 'php' in container.name][0]
        php_container.exec_run('apt install php-intl')

    def setup_drupal(self):
        with requests.Session() as s:
            headers = { 'Cookie' : 'wordpress_test_cookie=WP Cookie check' }
            headers = {}

            # Step 1
            url = 'http://localhost:8080/mw-config/index.php?page=Language'
            data = {'LanguageRequestTime' : str(time.time()).split('.')[0],
                    'uselang' : 'en',
                    'ContLang' : 'en',
                    'submit-continue' : 'Continue+→'}
            response = s.post(url, data=data, headers=headers)

            # Step 2
            url = 'http://localhost:8080/mw-config/index.php?page=Welcome'
            data = {'submit-continue' : 'Continue+→'}
            response = s.post(url, data=data, headers=headers)

            # Step 3
            url = 'http://localhost:8080/mw-config/index.php?page=DBConnect'
            data = {
                    "DBType": "mysql",
                    "mysql_wgDBserver": "mysql",
                    "mysql_wgDBname": "drupal",
                    "mysql_wgDBprefix": "",
                    "mysql__InstallUser": "drupal",
                    "mysql__InstallPassword": "password",
                    "sqlite_wgSQLiteDataDir": "/var/www/data",
                    "sqlite_wgDBname": "my_wiki",
                    "submit-continue": "Continue+→"
                    }
            response = s.post(url, data=data, headers=headers)
            response = s.post(url, data=data, headers=headers)

            # Step 4
            url = 'http://localhost:8080/mw-config/index.php?page=DBSettings'
            data = {
                    "mysql__SameAccount": "1",
                    "mysql_wgDBuser": "wikiuser",
                    "mysql_wgDBpassword": "",
                    "submit-continue": "Continue+→"
                    }
            response = s.post(url, data=data, headers=headers)

            # Step 5
            url = 'http://localhost:8080/mw-config/index.php?page=Name'
            data = {
                    "config_wgSitename": "Test",
                    "config__NamespaceType": "site-name",
                    "config_wgMetaNamespace": "MyWiki",
                    "config__AdminName": "test",
                    "config__AdminPassword": "password!@#$%^&*()",
                    "config__AdminPasswordConfirm": "password!@#$%^&*()",
                    "config__AdminEmail": "test@test.com",
                    "config__SkipOptional": "skip",
                    "submit-continue": "Continue+→"
                    }
            response = s.post(url, data=data, headers=headers)

            # Step 6
            url = 'http://localhost:8080/mw-config/index.php?page=Install'
            data = {'submit-continue' : 'Continue+→'}
            response = s.post(url, data=data, headers=headers)
            response = s.post(url, data=data, headers=headers)

            # Step 7: Get the local settings file
            url = 'http://localhost:8080/mw-config/index.php?localsettings=1'
            response = s.get(url, headers=headers)
            with open(os.path.join(self.configuration['web_app_sources'], 'LocalSettings.php'), 'w') as f:
                f.write(response.content.decode('utf-8'))

            # Step 8: Get the homepage to get the version number
            response = s.get('http://localhost:8080')
            versionCheck = re.compile(self.configuration['version_check']['regex'])
            return versionCheck.findall(response.content.decode('utf-8'))
