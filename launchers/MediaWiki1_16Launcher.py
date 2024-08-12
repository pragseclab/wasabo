from .WebAppLauncher import WebAppLauncher
from bs4 import BeautifulSoup
import fileinput
import requests
import time
import re
import os
import shutil
import stat

class MediaWiki1_16Launcher(WebAppLauncher):

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
        return self.setup_drupal()

    def prepare_files(self):
        # Copy settings file from default settings file
        destFile = os.path.join(self.configuration['web_app_sources'], 'config')
        os.chmod(destFile, 0o777)

    def setup_drupal(self):
        with requests.Session() as s:
            headers = { 'Cookie' : 'wordpress_test_cookie=WP Cookie check' }
            headers = {}

            # Step 1
            url = 'http://localhost:8080/config/index.php'
            data = {
                "Sitename": "Test",
                "EmergencyContact": "test@test.com",
                "LanguageCode": "en",
                "License": "none",
                "SysopName": "test",
                "SysopPass": "password!@#$%^&*()",
                "SysopPass2": "password!@#$%^&*()",
                "Shm": "none",
                "MCServers": "",
                "Email": "email_enabled",
                "Emailuser": "emailuser_enabled",
                "Enotif": "enotif_allpages",
                "Eauthent": "eauthent_enabled",
                "DBtype": "mysql",
                "DBserver": "mysql",
                "DBname": "drupal",
                "DBuser": "drupal",
                "DBpassword": "password",
                "DBpassword2": "password",
                "RootUser": "root",
                "RootPW": "",
                "DBprefix": "",
                "DBengine": "InnoDB",
                "DBschema": "mysql5-binary",
                "DBport": "5432",
                "DBpgschema": "mediawiki",
                "DBts2schema": "public",
                "SQLiteDataDir": "/var/www/html/../data",
                "DBprefix2": "",
                "DBport_db2": "50000",
                "DBdb2schema": "mediawiki",
                "DBcataloged": "cataloged",
                "DBprefix_ora": "",
                "DBdefTS_ora": "USERS",
                "DBtempTS_ora": "TEMP"
            }
            response = s.post(url, data=data, headers=headers)

            # Wait for the prompt to move the settings file
            response = s.get('http://localhost:8080/index.php', headers=headers)
            while('To complete the installation, move' not in response.content.decode('utf-8')):
                response = s.get('http://localhost:8080/index.php', headers=headers)

            # Step 2: Move the LocalSettings.php file from config/ to ./
            src = os.path.join(self.configuration['web_app_sources'], 'config/LocalSettings.php')
            dst = os.path.join(self.configuration['web_app_sources'], 'LocalSettings.php')
            shutil.move(src, dst)

            # Step 3: Get the homepage to get the version number
            response = s.get('http://localhost:8080')
            versionCheck = re.compile(self.configuration['version_check']['regex'])
            return versionCheck.findall(response.content.decode('utf-8'))
