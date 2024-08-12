from .WebAppLauncher import WebAppLauncher
from bs4 import BeautifulSoup
import fileinput
import requests
import time
import re
import os
import shutil
import stat

class Drupal10Launcher(WebAppLauncher):

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
            headers = { 'Cookie' : 'wordpress_test_cookie=WP Cookie check' }
            headers = {}

            # Step 1
            url = 'http://localhost:8080/core/install.php'
            data = {'langcode' : 'en', 'form_build_id' : '', 'form_id' : 'install_select_language_form', 'op' : 'Save and continue'}
            response = s.post(url, data=data, headers=headers)

            # Step 2
            url = 'http://localhost:8080/core/install.php?rewrite=ok&langcode=en'
            data = {'profile' : 'standard', 'form_build_id' : '', 'form_id' : 'install_select_profile_form', 'op' : 'Save and continue'}
            response = s.post(url, data=data, headers=headers)

            # Step 3
            url = 'http://localhost:8080/core/install.php?rewrite=ok&langcode=en&profile=standard'
            data = {'sqlite[database]' : 'sites/default/files/.ht.sqlite', 'sqlite[prefix]' : '',
                    'form_build_id' : '', 'form_id' : 'install_settings_form', 'op' : 'Save and continue'}
            response = s.post(url, data=data, headers=headers)

            # Start installation
            url = "http://localhost:8080/core/install.php?rewrite=ok&langcode=en&profile=standard&id=1&op=start"
            response = s.get(url, headers=headers)

            # Wait for the installation to finish
            time.sleep(2)
            url = 'http://localhost:8080/core/install.php?rewrite=ok&langcode=en&profile=standard&id=1&op=do_nojs&op=do&_format=json'
            response = s.post(url, allow_redirects=False)
            while(int(response.json()['percentage']) < 100):
                response = s.post(url, allow_redirects=False)
                time.sleep(2)

            # Step 4
            url = 'http://localhost:8080/core/install.php?rewrite=ok&langcode=en&profile=standard'
            data = {'site_name' : 'test', 'site_mail' : 'test@test.com', 'account[name]' : 'test', 'account[pass][pass1]' : 'password',
                    'account[pass][pass2]' : 'password', 'account[mail]' : 'test@test.com', 'site_default_country' : 'US', 'date_default_timezone' : 'UTC',
                    'enable_update_status_emails' : '1', 'form_build_id' : '', 'form_id' : 'install_configure_form', 'op' : 'Save and continue'}
            s.post(url, data=data, headers=headers)

            # Step 5 - Login
            url = 'http://localhost:8080/user/login'
            data = {'name' : 'test', 'pass' : 'password', 'form_id' : 'user_login_form', 'op' : 'Log+in'}
            s.post(url, data=data, headers=headers)

            # Get the status page for the version number
            response = s.get('http://localhost:8080/admin/reports/status')
            versionCheck = re.compile(self.configuration['version_check']['regex'])
            return versionCheck.findall(response.content.decode('utf-8'))
