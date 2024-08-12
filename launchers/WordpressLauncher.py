from .WebAppLauncher import WebAppLauncher
import fileinput
import requests
import time
import re
import os

class WordpressLauncher(WebAppLauncher):

    def __init__(self, configuration):
        super().__init__(configuration)
        self.containers = []

    def launch(self):
        # Set the volume location to that of the wordpress source location
        self.configuration['docker']['php']['volumes'] = {os.path.abspath(self.configuration['web_app_sources']) : {'bind' : '/var/www/html/'}}

        # Create the containers
        self.network = self.docker.create_network('wordpress')
        self.containers = self.launch_docker_containers(self.configuration['docker'])
        self.modify_wp_config()

        # Wait for MySQL container to accept connections before attempting to install Wordpress
        mysql_container = [container for container in self.containers if 'mysql' in container.name][0]
        self.wait_for_mysql(mysql_container)

        return self.setup_wp()

    def clean_up(self):
        # Remove all containers used
        for container in self.containers:
            container.kill()

        # Remove the container network
        self.network.remove()

    def wait_for_mysql(self, mysql_container):
        for i in range(0, 20):
            response = mysql_container.exec_run('mysql')
            if('ERROR 1045' in response.output.decode('utf-8')):
                break
            time.sleep(1)

    # Modify the wp-config.php file to set the proper DB values
    def modify_wp_config(self):
        # Check if the wp-config file is actually called wp-config-sample
        if((not os.path.exists(os.path.join(self.configuration['web_app_sources'], 'wp-config.php')) and
                (os.path.exists(os.path.join(self.configuration['web_app_sources'], 'wp-config-sample.php'))))):
            os.rename(os.path.join(self.configuration['web_app_sources'], 'wp-config-sample.php'), os.path.join(self.configuration['web_app_sources'], 'wp-config.php'))

        for line in fileinput.input(os.path.join(self.configuration['web_app_sources'], 'wp-config.php'), inplace=True):
            if('DB_NAME' in line):
                print("define( 'DB_NAME', getenv('WORDPRESS_DB_NAME') );")
            elif('DB_USER' in line):
                print("define( 'DB_USER', getenv('WORDPRESS_DB_USER') );")
            elif('DB_PASSWORD' in line):
                print("define( 'DB_PASSWORD', getenv('WORDPRESS_DB_PASSWORD') );")
            elif('DB_HOST' in line):
                print("define( 'DB_HOST', getenv('WORDPRESS_DB_HOST') );")
            else:
                print(line, end='')

    # Send post requests to go through Wordpress installation and confirm
    def setup_wp(self):
        wp_login = 'http://localhost:8080/wp-login.php'
        wp_admin = 'http://localhost:8080/wp-admin'
        wp_update = 'http://localhost:8080/wp-admin/update-core.php'
        username = 'wordpress'
        password = 'password'

        with requests.Session() as s:
            headers = { 'Cookie' : 'wordpress_test_cookie=WP Cookie check' }

            data = {'weblog_title' : 'test', 'user_name' : 'wordpress', 'admin_password' : 'password', 'admin_password2' : 'password',
                    'pw_weak' : 'on', 'admin_email' : 'test@test.com', 'Submit' : 'Install+WordPress', 'language' : ''}
            s.post('http://localhost:8080/wp-admin/install.php?step=2', headers=headers, data=data)

            data = { 'log' : username, 'pwd' : password, 'wp-submit' : 'Log In', 'redirect_to' : wp_admin, 'testcookie' : '1' }

            s.post(wp_login, headers=headers, data=data)

            # Get the webpage containing the version string specified in the configuration file
            response = s.get(self.configuration['version_check']['url'])
            content = response.content.decode('utf-8')

            versionCheck = re.compile(self.configuration['version_check']['regex'])
            return versionCheck.findall(content)

if __name__ == '__main__':
    import json
    with open('../config/wordpress/wordpress5_6_1.json') as f:
        config = json.load(f)

    launcher = WordpressLauncher(config)
    launcher.launch()
    launcher.clean_up()
