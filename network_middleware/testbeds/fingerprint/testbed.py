import docker
import requests
import logging

class Testbed():

    def __init__(self):
        self.client = docker.from_env()

    def launch_scan(self, image, command):
        try:
            output = self.client.containers.run(image,
                                                command,
                                                network="fingerprint",
                                                environment={"http_proxy" : "http://mitmproxy:8080",
                                                            "https_proxy" : "http://mitmproxy:8080"},
                                                auto_remove=True,
                                                stderr=True)
        except Exception as e:
            logging.error(e)
            output = ""
        return output

    def log_results(self, fingerprinting_tool, url, webapp_name, config_notes, fingerprint_result):
        with open(f"testbeds/fingerprint/results/{fingerprinting_tool}.csv", 'a+') as f:
            if(type(fingerprint_result) == str):
                f.write(f"{url};{webapp_name};{config_notes};{fingerprint_result.replace(';', '|').encode()}\n")
            else:
                f.write(f"{url};{webapp_name};{config_notes};{fingerprint_result.decode('utf-8').replace(';', '|').encode()}\n")

    def run_test(self, webapp_name, url):

        # # ### Whatweb
        # whatweb_output = self.launch_scan("whatweb:latest", "--log-json /dev/stdout %s" % url)
        # self.log_results("whatweb", url, webapp_name, "guess,selenium", whatweb_output)

        # # ### Wappalyzer
        # wappalyzer_output = self.launch_scan("wappalyzer:latest", "%s" % url)
        # self.log_results("wappalyzer", url, webapp_name,  "guess,selenium", wappalyzer_output)

        ### BlindElephant
        # blindelephant_output = self.launch_scan("blindelephant:latest", f"{url} {webapp_name if webapp_name else 'guess'}")
        blindelephant_output = self.launch_scan("blindelephant:latest", f"{url} guess")
        self.log_results("blindelephant", url, webapp_name, "guess,selenium", blindelephant_output)

        # ### VersionInferrer
        # versioninferrer_output = self.launch_scan("versioninferrer:latest", "--json-only %s" % url)
        # self.log_results("versioninferrer", url, webapp_name, "guess,selenium", versioninferrer_output)

        # # # ### WPScan
        # if(webapp_name == 'wordpress'):
        #     try:
        #         response = requests.get(url)
        #         redirect_url = response.url
        #     except:
        #         redirect_url = url
        #     wpscan_output = self.launch_scan("wpscan:latest", f"-f JSON --url {redirect_url}")
        #     self.log_results("wpscan", url, webapp_name, "guess,nowhitespace", wpscan_output)
