import ast
import csv
import json
import os
import re
import sys
from tkinter.ttk import Separator
import pandas as pd

def parseBlindelephant(fingerprint_results):
    bestGuessCheck = re.compile("Best Guess: +([\d.]+)")
    looseVersionCheck = re.compile("LooseVersion \(\'+([a-zA-Z\d.]+)\'\)")

    results = []

    for row in fingerprint_results:
        bestGuess = bestGuessCheck.findall(row)
        looseVersions = looseVersionCheck.findall(row)
        url = row.split(';')[0]
        run_type = 'plugin,default' if row.split(';')[2] == '' else row.split(';')[2]
        run_type = run_type.replace('guess,heavy', 'guess,default')
        for version in looseVersions:
            if(bestGuess != [] and version == bestGuess[0]):
                results.append(('blindelephant', url, row.split(';')[1], run_type, version, True))
            else:
                results.append(('blindelephant', url, row.split(';')[1], run_type, version, False))

        if(len(looseVersions) == 0):
            results.append(('blindelephant', url, row.split(';')[1], run_type, None, False))
            if("perikentimatos.eu" in url):
                print(results[-1])

    return results

def parseVersioninferrer(fingerprint_results):
    results = []

    for row in fingerprint_results:
        url = row.split(';')[0]
        run_type = 'guess,default' if row.split(';')[2] == '' else row.split(';')[2]

        vi_results = row.split(';')[-1]
        vi_results = json.loads(eval(vi_results).decode("utf-8"))

        if("result" not in vi_results):
            results.append(('versioninferrer', url, row.split(';')[1], run_type, None, False))
            continue

        for guess in vi_results["result"]:
            guess = f'{guess["software_version"]["software_package"]["name"]} {guess["software_version"]["name"]}'
            guess = guess.replace("Joomla! CMS™", "Joomla").lower()
            results.append(('versioninferrer', url, row.split(';')[1], run_type, guess, False))

    return results


# def parseVersioninferrer(fingerprint_results):
#     # guessCheck = re.compile("Guess '+([a-zA-Z\s\!\d.\\\\]+)\(")
#     guessCheck = re.compile("Guess [\s\\']*([\w\s.\\!]*)\(")

#     results = []

#     for row in fingerprint_results:
#         url = row.split(';')[0]
#         run_type = 'guess,default' if row.split(';')[2] == '' else row.split(';')[2]

#         vi_results = row.split(';')[-1]
#         print(vi_results)
#         return
#         guesses = re.findall("Guess [\s\\']*([\w\s.\\!]*)\(", eval(vi_results).decode("utf-8"))
#         # guesses = guessCheck.findall(vi_results)
#         for i in range(len(guesses)):
#             print(guesses)
#             guess = guesses[i]
#             guesses[i] = (guess.split(' ')[0] + '-' + guess.split(' ')[-2]).lower()
#             results.append(('versioninferrer', url, row.split(';')[1], run_type, guesses[i].replace('joomla!', 'joomla'), False))

#         if(len(guesses) == 0):
#             results.append(('versioninferrer', url, row.split(';')[1], run_type, None, False))
#             # if("judiciary" in url):
#             #     print(row)

#     return results

def parseWhatweb(fingerprint_results):
    results = []
    run_types = set()

    nameDict = {
        'wordpress' : 'WordPress',
        'mediawiki' : 'MediaWiki',
        'drupal' : 'Drupal',
        'joomla' : 'Joomla',
        'phpmyadmin' : 'phpMyAdmin'
    }

    for row in fingerprint_results:
        run_type = row.split(';')[2]
        webapp = row.split(';')[1]
        url = row.split(';')[0]
        try:
            webapp = nameDict[webapp]
        except Exception as e:
            print(row)
            raise e
        run_types.add(run_type)
        guesses = ast.literal_eval(row.split(';')[-1].strip()).decode('utf-8').split('\n')
        guesses = [g for g in guesses if (g != '' and g[0] == '{')]
        try:
            result = json.loads(guesses[-1])
        except Exception as e:
            pass

        # Cases for each web app
        parsedGuesses = []
        if(webapp in result['plugins'].keys()):
            if('version' in result['plugins'][webapp].keys()):
                for g in result['plugins'][webapp]['version']:
                    if(g[0] == '['):
                        parsedGuesses.append('%s-%s' % (webapp.lower(), g[2:-2]))
                    else:
                        parsedGuesses.append('%s-%s' % (webapp.lower(), g))
            else:
                parsedGuesses.append(webapp.lower())
        else:
            parsedGuesses.append(None)

        for guess in parsedGuesses:
            results.append(('whatweb', url, row.split(';')[1], run_type, guess, False))

    return results

def parseWappalyzer(fingerprint_results):
    results = []

    for row in fingerprint_results:
        run_type = row.split(';')[2]
        webapp = row.split(';')[1]
        url = row.split(';')[0]
        guesses = ast.literal_eval(row.split(';')[-1])
        try:
            result = json.loads(guesses)
        except Exception as e:
            continue
            pass

        parsedGuesses = []
        for technology in result['technologies']:
            if(webapp == technology['slug'].lower()):
                if(technology['version'] != None):
                    parsedGuesses.append("%s-%s" % (webapp, technology['version']))
                else:
                    parsedGuesses.append(webapp)

        # If there were no guesses, then append one NULL guess
        if(len(parsedGuesses) == 0):
            parsedGuesses.append(None)

        for guess in parsedGuesses:
            results.append(('wappalyzer', url, row.split(';')[1], run_type, guess, False))

    return results

def parseMetasploit(fingerprint_results):
    results = []
    wordpress_regex = re.compile("Detected Wordpress +([\d.]+)")
    joomla_regex = re.compile("Joomla version: +([\d.]+)")

    for row in fingerprint_results:
        run_type = row.split(';')[2]
        webapp = row.split(';')[1]
        output = row.split(';')[-1]
        url = row.split(';')[0]

        if(webapp == 'wordpress'):
            guesses = wordpress_regex.findall(output)
        elif(webapp == 'joomla'):
            output = ast.literal_eval(output.strip()).decode('utf-8')
            guesses = joomla_regex.findall(output)

        if(len(guesses) == 0):
            guesses.append(None)

        for guess in guesses:
            results.append(('metasploit', url, row.split(';')[1], run_type, guess, False))

    return results

totalResults = []
data_dir = './results/'
for output_file in os.listdir(data_dir):
    if('old' in output_file):
        continue

    results_df = pd.read_csv(os.path.join(data_dir, output_file), sep=';', header=None)
    print(output_file)
    print(results_df.shape[0])
    print(results_df[results_df[0].str.contains("ohsheglows")])
    results_df = results_df.drop_duplicates([0,1,2], keep="last")
    results = results_df.to_csv(header=False, index=False, sep=';', quoting=csv.QUOTE_NONE).split('\n')
    if(results[-1] == ''):
        results = results[:-1]
    print(results_df.shape[0])
    print()

    if('blindelephant' in output_file):
        parsed_results = parseBlindelephant(results)
    elif('versioninferrer' in output_file):
        parsed_results = parseVersioninferrer(results)
    elif('whatweb' in output_file):
        parsed_results = parseWhatweb(results)
    elif('wappalyzer' in output_file):
        parsed_results = parseWappalyzer(results)
    elif('metasploit' in output_file):
        parsed_results = parseMetasploit(results)
    else:
        continue

    totalResults+=parsed_results

with open("real_world_results.csv", 'w') as f:
    f.write('tool;url;web_app;run_type;results;best_result\n')
    for result in totalResults:
       f.write('%s\n' % ';'.join([str(r) for r in result]))
