import docker
import os

class docker_client:

    def __init__(self):
        self.client = docker.from_env()

    def build_image(self, docker_file):
        return

    def launch_container(self, image, name=None, network=None, volumes=[], environment=[], ports={}):
        container = self.client.containers.run(image, name=name, network=network, environment=environment,
                                               volumes=volumes, ports=ports,
                                               auto_remove=True, detach=True, remove=True)
        return container

    def stop_container(self, name):
        return

    def destroy_container(self, name):
        return

    def get_images(self):
        return self.client.images.list()

    def build_image(self, dockerfile_path, tag):
        self.client.images.build(path='./', dockerfile=dockerfile_path, tag=tag, quiet=True)

    def create_network(self, name):
        return self.client.networks.create(name, check_duplicate=True)

    def get_container_health(self, name):
        try:
            return self.client.api.inspect_container(name)['State']['Health']['Status']
        except:
            return None

if __name__ == '__main__':
    client = docker_client()

    # mysql_container = client.launch_container('mysql/mysql-server:5.6', name='mysql_container', network='wordpress',
    #                                           environment=["MYSQL_DATABASE=wordpress", "MYSQL_ROOT_PASSWORD=password",
    #                                                        "MYSQL_USER=wordpress", "MYSQL_PASSWORD=password"],
    #                                           )

    print(client.client.api.inspect_container('mysql_5.6')['State']['Health']['Status'])
