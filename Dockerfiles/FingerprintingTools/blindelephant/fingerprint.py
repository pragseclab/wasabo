import sys
from blindelephant.Fingerprinters import WebAppFingerprinter
from blindelephant.Fingerprinters import WebAppGuesser

if(sys.argv[2] == 'guess'):
    g = WebAppGuesser(sys.argv[1])
    g._host_down_errors = -900000
    apps = g.guess_apps()
    for app in apps:
        # LooseVersion ('1.11.0')
        print("LooseVersion (\'%s\')" % app)
else:
    if(len(sys.argv) == 4):
        fp = WebAppFingerprinter(sys.argv[1], sys.argv[2], num_probes=int(sys.argv[3]))
    else:
        fp = WebAppFingerprinter(sys.argv[1], sys.argv[2])
    # fp.HOST_DOWN_THRESHOLD = 10
    fp._host_down_errors = -900000
    fp.fingerprint()
    print(fp.ver_list)
