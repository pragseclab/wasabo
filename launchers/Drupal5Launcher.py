from .WebAppLauncher import WebAppLauncher
from bs4 import BeautifulSoup
import fileinput
import requests
import time
import re
import os
import shutil
import stat
import json

class Drupal5Launcher(WebAppLauncher):

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
        destFile = os.path.join(self.configuration['web_app_sources'], 'sites/default/settings.php')
        os.chmod(destFile, 0o777)
        os.chmod(os.path.join(self.configuration['web_app_sources'], 'sites/default'), 0o777)

    def setup_drupal(self):
        with requests.Session() as s:
            headers = {'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'}

            # Step 1
            url = 'http://localhost:8080/install.php?profile=default&locale=en'
            data = {
                "db_type": "mysql",
                "db_path": "drupal",
                "db_user": "drupal",
                "db_pass": "password",
                "db_host": "mysql",
                "db_port": "",
                "db_prefix": "",
                "op": "Save+configuration",
                "form_id": "install_settings_form"
            }
            response = s.post(url, data=data, headers=headers)

            # Step 2
            url = 'http://localhost:8080/?q=user/register'
            data = {
                "name": "test",
                "mail": "test@test.com",
                "form_id": "user_register",
                "op": "Create+new+account"
            }
            response = s.post(url, data=data, headers=headers)

            # Step 3
            url = 'http://localhost:8080/?q=user/1/edit'
            data = {
                "name" : "test",
                "mail" : "test@test.com",
                "pass[pass1]" : "password",
                "pass[pass2]" : "password",
                "status" : "1",
                "form_token" : "b6b559171a175f051ad7af308584e151",
                "form_id" : "user_edit",
                "signature" : "",
                "timezone" : "0",
                "op" : "Submit"
            }
            response = s.post(url, data=data, headers=headers)

            # Get the status page for the version number
            response = s.get('http://localhost:8080/?q=admin/logs/status')
            versionCheck = re.compile(self.configuration['version_check']['regex'])
            return versionCheck.findall(response.content.decode('utf-8'))

        return
