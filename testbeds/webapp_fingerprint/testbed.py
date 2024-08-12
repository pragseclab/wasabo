from ..testbed import Testbed
import docker

class Testbed(Testbed):

    def __init__(self, webapp_name, webapp_version):
        super().__init__('WebAppFingerprint')
        self.webapp_name = webapp_name
        self.webapp_version = webapp_version
        self.client = docker.from_env()

    def log_results(self, fingerprinting_tool, webapp_version, setup_result, config_notes, fingerprint_result):
        with open(f"testbeds/webapp_fingerprint/results/{fingerprinting_tool}.csv", 'a+') as f:
            f.write(f"{webapp_version};{setup_result};{config_notes};{fingerprint_result.decode('utf-8').replace(';', '|').encode()}\n")

    def run_test(self, setup_result):
        be_nodes = {
            'drupal' : 382501,
            'joomla' : 9693,
            'mediawiki' : 186080,
            'phpmyadmin' : 126019,
            'wordpress' : 1000000
        }

	host_port = ""

        ### BlindElephant

        blindelephant_output = self.client.containers.run("blindelephant:latest", f"http://{host_port} guess", remove=True)
        self.log_results("blindelephant", self.webapp_version, setup_result, "guess,default", blindelephant_output)

        blindelephant_output = self.client.containers.run("blindelephant:latest", "http://{host_port} %s" % self.webapp_name, remove=True)
        self.log_results("blindelephant", self.webapp_version, setup_result, "plugin,default", blindelephant_output)

        blindelephant_output = self.client.containers.run("blindelephant:latest", "http://{host_port} %s %d" % (self.webapp_name, be_nodes[self.webapp_name]), remove=True)
        self.log_results("blindelephant", self.webapp_version, setup_result, "plugin,heavy", blindelephant_output)
