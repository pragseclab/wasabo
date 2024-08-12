import sys
import os
import os.path
import json
import time
import importlib
import shutil
import argparse

WEB_APP_CONFIGS_DIR = 'webapp_configs'
WEB_APP_SOURCES_DIR = 'webapp_sources'
LAUNCHERS_DIR = 'launchers'
TESTS_DIR = 'testbeds'

# Load and verify configuration file for specified web application
def read_config(web_app):
    config_file_path = os.path.join(WEB_APP_CONFIGS_DIR, web_app + '.json')

    if(not os.path.exists(config_file_path)):
        return None

    with open(config_file_path, 'r') as config_file:
        web_app_config = json.load(config_file)

    return web_app_config

def main(web_app, testbed):
    # Load configuration file
    configuration = read_config(web_app)
    if(not configuration):
        print('Config file does not exist for specified web application')
        return

    # Import the specified testbed
    testbed_module = importlib.import_module('testbeds.' + testbed)
    testbed_class = getattr(testbed_module, 'Testbed')
    testbed = testbed_class(web_app.split("/")[0], web_app.split('/')[1])

    # Copy the current web app source code to tmp directory
    shutil.copytree(os.path.join(WEB_APP_SOURCES_DIR, web_app), 'staged_webapp')
    configuration["web_app_sources"] = 'staged_webapp'

    # Import the launcher class for this application
    launcher_module = importlib.import_module('launchers.' + configuration['launcher'])
    launcher_class = getattr(launcher_module, configuration['launcher'])
    launcher = launcher_class(configuration)

    # Launch web application and run specified test
    try:
        result = launcher.launch()
        if(result != []):
            print(result)
            testbed.run_test(result)
        else:
            print('Error: %s: %s' % (web_app.split('/')[-1], result))
    except Exception as e:
        print(e)
        # print('Errored Out')
    finally:
        launcher.clean_up()
        shutil.rmtree('staged_webapp')

def process_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("webapp_version",
                        nargs="?",
                        help="Single web application version to launch and exercise")
    parser.add_argument("-w", "--output-file",
                        type=str,
                        help="File to write probe outputs to. This argument is required if in record mode.",
                        default=None)
    parser.add_argument("-r", "--versions-file",
                        type=str,
                        help="File containing multiple web application versions to launch and exercise")
    parser.add_argument("-t", "--testbed",
                        type=str,
                        help="Testbed to run in the 'testbeds' folder. Defaults to test_webapp",
                        default="test_webapp")
    args = vars(parser.parse_args())

    if((args["webapp_version"] == None and args["versions_file"] == None)):
        parser.print_help()
        return None

    # Add .testbed to end of whatever the testbed provided was
    args["testbed"] = args["testbed"] + ".testbed"

    return args

if(__name__ == '__main__'):
    args = process_args()
    if(args == None):
        sys.exit(1)

    if(args["versions_file"] == None):
        main(args["webapp_version"], args["testbed"])
    else:
        with open(args["versions_file"], 'r') as f:
            versions = [version.strip() for version in f.readlines()]

        for version in versions:
            if(not os.path.exists(os.path.join('webapp_sources', version))):
                continue
            print('%s: ' % version.split('/')[-1], end='')
            main(version, args["testbed"])
