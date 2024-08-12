from .WebAppLauncher import WebAppLauncher
from bs4 import BeautifulSoup
import fileinput
import requests
import time
import re
import os
import shutil
import stat

class PhpMyAdminLauncher(WebAppLauncher):

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
        return self.check_version()

    def replaceLineInFile(self, fileName, searchExp, replaceExp):
        for line in fileinput.input(fileName, inplace=1):
            if searchExp in line:
                line = line.replace(searchExp,replaceExp)
            print(line, end='')

    def prepare_files(self):
        # Copy settings file from default settings file
        sourceFile = os.path.join(self.configuration['web_app_sources'], 'config.sample.inc.php')
        destFile = os.path.join(self.configuration['web_app_sources'], 'config.inc.php')

        if(not os.path.exists(destFile)):
            shutil.move(sourceFile, destFile)
        self.replaceLineInFile(destFile, "$cfg['Servers'][$i]['host'] = 'localhost';", "$cfg['Servers'][$i]['host'] = 'mysql';")
        self.replaceLineInFile(destFile, "$cfgServers[1]['host']          = 'localhost';", "$cfgServers[1]['host']          = 'mysql';")
        self.replaceLineInFile(destFile, "$cfgServers[1]['user']          = 'root';", "$cfgServers[1]['user']          = 'phpmyadmin';")
        self.replaceLineInFile(destFile, "$cfgServers[1]['password']      = '';", "$cfgServers[1]['password']      = 'password';")
        self.replaceLineInFile(destFile, "$cfg['blowfish_secret'] = ''; /* YOU MUST FILL IN THIS FOR COOKIE AUTH! */",
                "$cfg['blowfish_secret'] = 'secret'; /* YOU MUST FILL IN THIS FOR COOKIE AUTH! */")


    def check_version(self):
        with requests.Session() as s:
            headers = {'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'}

            # Step 1 - Get the login page and get hidden elements
            url = 'http://localhost:8080'
            response = s.get(url)
            soup = BeautifulSoup(response.content.decode('utf-8'), features="html.parser")
            try:
                set_session = soup.findAll('input', attrs={'name' : 'set_session'})[0].attrs['value']
            except:
                set_session = ''
            try:
                token = soup.findAll('input', attrs={'name' : 'token'})[0].attrs['value']
            except:
                token = ''

            url = 'http://localhost:8080/index.php'
            data = {'pma_username' : 'phpmyadmin', 'pma_password' : 'password', 'server' : '1', 'target' : 'index.php', 'set_session' : set_session,
                    'token' : token}
            response = s.post(url, data=data, headers=headers)

            # Get the status page for the version number
            response = s.get('http://localhost:8080/index.php')
            versionCheck = re.compile(self.configuration['version_check']['regex'])
            return versionCheck.findall(response.content.decode('utf-8'))
