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
import traceback

class Drupal6Launcher(WebAppLauncher):

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
            return self.setup_drupal()
        except:
            traceback.print_exc()

    def prepare_files(self):
        # Copy settings file from default settings file
        sourceFile = os.path.join(self.configuration['web_app_sources'], 'sites/default/default.settings.php')
        destFile = os.path.join(self.configuration['web_app_sources'], 'sites/default/settings.php')
        shutil.copyfile(sourceFile, destFile)
        st = os.stat(sourceFile)
        os.chown(destFile, st[stat.ST_UID], st[stat.ST_GID])
        os.chmod(destFile, 0o777)
        os.chmod(os.path.join(self.configuration['web_app_sources'], 'sites/default'), 0o777)

        # Create public download folder
        publicDownloadFolder = os.path.join(self.configuration['web_app_sources'], 'sites/default/files')
        if(os.path.exists(publicDownloadFolder)):
            shutil.rmtree(publicDownloadFolder)
        # os.mkdir(publicDownloadFolder)
        # os.chown(publicDownloadFolder, st[stat.ST_UID], st[stat.ST_GID])

    def setup_drupal(self):
        with requests.Session() as s:
            headers = {'User-Agent' : 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:87.0) Gecko/20100101 Firefox/87.0'}

            # Step 1
            url = 'http://localhost:8080/install.php?profile=default&locale=en'
            data = {
                "db_type": "mysqli",
                "db_path": "drupal",
                "db_user": "drupal",
                "db_pass": "password",
                "db_host": "mysql",
                "db_port": "",
                "db_prefix": "",
                "op": "Save+and+continue",
                "form_build_id": "form-PJaGKL-Ei914doJ_xOq7QizrtNdxdl4Tm4ZSywyEqy4",
                "form_id": "install_settings_form"
            }
            response = s.post(url, data=data, headers=headers)

            # # Wait for the installation to finish
            time.sleep(2)
            url = 'http://localhost:8080/install.php?profile=default&locale=en&id=1&op=do'
            response = s.post(url, headers=headers)
            content = json.loads(response.content.decode('utf-8').replace('/', '').replace('\\', ''))
            while(int(content['percentage']) < 100):
                response = s.post(url)
                content = json.loads(response.content.decode('utf-8').replace('/', '').replace('\\', ''))
                time.sleep(2)

            # Try extra get request
            s.get('http://localhost:8080/install.php?locale=en&profile=default&id=1&op=finished')

            # Step 2
            url = 'http://localhost:8080/install.php?profile=default&locale=en'
            data = {
                "site_name": "test",
                "site_mail": "test@test.com",
                "account[name]": "test",
                "account[mail]": "test@test.com",
                "account[pass][pass1]": "password",
                "account[pass][pass2]": "password",
                "date_default_timezone": "-14400",
                "clean_url": "1",
                "form_build_id": "form-_O2_i2tST4ahwW4bG_CZS-K9IPr0Ds1OjznCXlVLgJM",
                "form_id": "install_configure_form",
                "op": "Save+and+continue"
            }
            response = s.post(url, data=data, headers=headers)

            # Get the home page
            response = s.get('http://localhost:8080/')

            # Get the status page for the version number
            response = s.get('http://localhost:8080/admin/reports/status')
            versionCheck = re.compile(self.configuration['version_check']['regex'])
            return versionCheck.findall(response.content.decode('utf-8'))

        return
