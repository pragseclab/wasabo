# WebAppTester

Web application testing infrastructure that utilizes Docker to efficiently spin up and tear down specific versions of PHP web applications. This tool is broken up into three main components, listed below:

* **Dockerfiles**: Dockerfiles used to build base images required to run PHP web applications. Typically these include Apache/PHP images and MySQL images. Additionally, Dockerfiles to create some of the web application fingerprinting tool images used in the paper are included here.
* **webapp_sources**: Subdirectories containing the source code of each desired web application. Format of subdirections is webAppName/webAppName-webAppVersion
* **webapp_configs**: Subdirectories containing configuration files for each web application version. Format of subdirectories is webAppName/webAppName-webAppVersion.json
* **testbeds**: Scripts which are executed after each web application is brought online. New testbeds can be created by copying the test_webapp example testbed, and adding desired code

## Installation

First, install all dependencies using the pip requirements file: `pip3 install -r requirements.txt`

Next, download any web application sources you are interested in running, and place the downloaded folders into the `webapp_sources` directory using the directory naming convention listed above. For example, if you downloaded Wordpress version 4.5, the file path would be as follows: `webapp_sources/wordpress/wordpress-4.5/`.
You do not need to worry about the webapp_configs directory unless you are planning to add support for new web applications.

Ideally, this would be the entirety of the installation process. The building of Dockerfiles should be done automatically at runtime if the Docker image is not found. However, I haven't really tested this thoroughly yet. So if you find it doesn't work properly you can build the Docker images yourself. Just be sure to match the image name that appears in the configuration file of the web application you're interested in. 

For example, if you wanted to run Wordpress version 4.5, you need to prepare the Docker images for PHP 5.6 and MySQL 5.6. The former is built with the Dockerfile locally with the commands:
```
cd Dockerfiles
sudo Docker build -t base_images:php_5.6 . -f php_5.6
```
And you can download the latter using the following command:
```
sudo Docker pull mysql/mysql-server:5.6
```

## Usage
```
usage: wasabo.py [-h] [-w OUTPUT_FILE] [-r VERSIONS_FILE] [-t TESTBED] [webapp_version]

positional arguments:
  webapp_version        Single web application version to launch and exercise

optional arguments:
  -h, --help            show this help message and exit
  -w OUTPUT_FILE, --output-file OUTPUT_FILE
                        File to write probe outputs to. This argument is required if in record mode.
  -r VERSIONS_FILE, --versions-file VERSIONS_FILE
                        File containing multiple web application versions to launch and exercise
  -t TESTBED, --testbed TESTBED
                        Testbed to run in the 'testbeds' folder. Defaults to test_webapp
```
