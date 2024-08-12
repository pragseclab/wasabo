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

class Drupal4Launcher(WebAppLauncher):

    def __init__(self, configuration):
        super().__init__(configuration)
        self.containers = []

    def launch(self):
        # Set the volume location to that of the wordpress source location
        self.configuration['docker']['php']['volumes'] = {os.path.abspath(self.configuration['web_app_sources']) : {'bind' : '/var/www/html/',
                                                                                                                    'mode' : 'rw'}}
        self.configuration['docker']['mysql']['volumes'] = {os.path.abspath(self.configuration['web_app_sources']) : {'bind' : '/var/www/html/',
                                                                                                                    'mode' : 'rw'}}

        # Create the containers
        self.network = self.docker.create_network('wordpress')
        self.containers = self.launch_docker_containers(self.configuration['docker'])

        # Wait for MySQL container to accept connections before attempting to install Wordpress
        self.mysql_container = [container for container in self.containers if 'mysql' in container.name][0]
        self.wait_for_mysql(self.mysql_container)

        self.prepare_files()
        return self.setup_drupal()

    def replaceLineInFile(self, fileName, searchExp, replaceExp):
        for line in fileinput.input(fileName, inplace=1):
            if searchExp in line:
                line = line.replace(searchExp,replaceExp)
            print(line, end='')

    def prepare_files(self):
        # destFile = os.path.join(self.configuration['web_app_sources'], 'sites/default/settings.php')
        # os.chmod(destFile, 0o777)
        # os.chmod(os.path.join(self.configuration['web_app_sources'], 'sites/default'), 0o777)

        # Load the database into mysql
        if(os.path.exists(os.path.join(self.configuration['web_app_sources'], 'database/database.4.1.mysql'))):
            mysqlFile = 'database.4.1.mysql'
        else:
            mysqlFile = 'database.mysql'

        # Test removing the offending line from the mysql file
        self.replaceLineInFile(os.path.join(self.configuration['web_app_sources'], 'database', mysqlFile), ') TYPE=MyISAM;', ');')
        self.mysql_container.exec_run('/bin/sh -c \'mysql -udrupal -ppassword drupal < /var/www/html/database/%s\'' % mysqlFile)

        # Change settings.php
        if(os.path.exists(os.path.join(self.configuration['web_app_sources'], 'sites/default/settings.php'))):
            settingsFile = os.path.join(self.configuration['web_app_sources'], 'sites/default/settings.php')
            searchExp = '$db_url = \'mysql://username:password@localhost/databasename\';'
            self.replaceLineInFile(settingsFile, '$db_url = \'mysql://username:password@localhost/database\';',
                    '$db_url = \'mysql://drupal:password@mysql/drupal\';')
            self.replaceLineInFile(settingsFile, '$base_url = \'http://localhost\';', '$base_url = \'http://localhost:8080\';')
        else:
            settingsFile = os.path.join(self.configuration['web_app_sources'], 'includes/conf.php')
            searchExp = '$db_url = "mysql://drupal:drupal@localhost/drupal";'
            self.replaceLineInFile(settingsFile, '$base_url = "http://localhost";', '$base_url = "http://localhost:8080";')

        # os.chmod(settingsFile, 0o777)
        self.replaceLineInFile(settingsFile, searchExp, '$db_url = \'mysql://drupal:password@mysql/drupal\';')

    def setup_drupal(self):
        with requests.Session() as s:
            headers = {'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'}

            # Step 1
            url = 'http://localhost:8080/?q=user/register'
            data = {
                "edit[name]": "test",
                "edit[mail]": "test@test.com",
                "edit[form_id]": "user_register",
                "op": "Create+new+account"
            }
            response = s.post(url, data=data, headers=headers)

            # Step 3
            # url = 'http://localhost:8080/?q=user/1/edit'
            # data = {
            #     "name" : "test",
            #     "mail" : "test@test.com",
            #     "pass[pass1]" : "password",
            #     "pass[pass2]" : "password",
            #     "status" : "1",
            #     "form_token" : "b6b559171a175f051ad7af308584e151",
            #     "form_id" : "user_edit",
            #     "signature" : "",
            #     "timezone" : "0",
            #     "op" : "Submit"
            # }
            # response = s.post(url, data=data, headers=headers)

            # Get the status page for the version number
            response = s.get('http://localhost:8080')
            versionCheck = re.compile(self.configuration['version_check']['regex'])
            return versionCheck.findall(response.content.decode('utf-8'))

        return
