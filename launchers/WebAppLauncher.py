import sys
import os
import os.path
import json
import time
from .DockerClient import docker_client

class WebAppLauncher:

    def __init__(self, configuration):
        self.docker = docker_client()
        self.configuration = configuration

    def clean_up(self):
        # Remove all containers used
        for container in self.containers:
            container.kill()

        # Remove the container network
        self.network.remove()

    def build_images(self, docker_config):
        current_images = self.docker.get_images()
        current_image_tags = set([str(image.tags[0]) if len(image.tags) > 0 else "" for image in current_images])

        for key, value in docker_config.items():
            if(value['image_name']not in current_image_tags):
                print('Building image: %s' % key)
                self.docker.build_image('Dockerfiles/' + value['image_name'], value['image_name'])

    def launch_docker_containers(self, docker_config):
        containers = []
        self.build_images(docker_config)

        for name, value in docker_config.items():
            container = self.docker.launch_container(value['image_name'],
                                                name=name,
                                                network='wordpress',
                                                environment=value['environment'] if 'environment' in value else None,
                                                ports=value['ports'] if 'ports' in value else None,
                                                volumes=value['volumes'] if 'volumes' in value else None)
            containers.append(container)

        return containers

    def wait_for_mysql(self, mysql_container):
        for i in range(0, 20):
            response = mysql_container.exec_run('mysql')
            if('ERROR 1045' in response.output.decode('utf-8')):
                break
            time.sleep(1)
