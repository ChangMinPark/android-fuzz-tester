import re
import os
from argparse import ArgumentParser
import numpy as np

# Takes a path containing APKs to test
parser = ArgumentParser(description='Parse logs and results after the fuzz testing')
parser.add_argument('LOG_PATH', action='store', \
        help='A directory containing logss (e.g., 2021-11-28 00:53:04.895557)')
args = parser.parse_args()
log_path = args.LOG_PATH


# Log patterns (API 27)
PATTERN = re.compile(r"""^.*(?P<transaction>B[A-Z]_TRANSACTION):\s+\[Interface\stoken\]\s+(?P<class>.+)\s+\[code\]\s+(?P<code>[a-zz\d]+)\s*$""",re.VERBOSE)




def find_ssi(log_file: str, pid: str=None) -> set:
    found = set()
    with open(log_file, 'r', errors='ignore') as f:
        for line in f.readlines():
            line = line.strip()

            # Parse only for the given PID
            if pid and not pid in line:
                continue

            match = PATTERN.match(line)
            if match == None:
                continue

            transaction = match.group('transaction')
            class_name = match.group('class')
            code = match.group('code')
        
            found.add((transaction, class_name, code))

    return found



def find_ui(log_file: str) -> set:
    found = set()
    with open(log_file, 'r', errors='ignore') as f:
        for line in f.readlines():
            split_line = line.strip().split('___')
            if len(split_line) != 2:
                continue

            found.add((split_line[0], split_line[1]))

    return found





def main():
    
    # SSIs before testing
    ssi_log = 'logcat_base_8.1.0_r1'
    ssi_before = find_ssi(ssi_log, pid=None)

    # Log file nmaes
    adb_log = 'adb_logcat_emulator-'
    uis_log = 'uis_traversed_emulator-'


    pkg_dirs = os.listdir(log_path)
    all_ui = {}
    all_ssi = {}
    for pkg_dir in pkg_dirs:
        path_pkg = os.path.join(log_path, pkg_dir)
        if not os.path.isdir(path_pkg):
            continue

        all_ui[pkg_dir] = {}
        all_ssi[pkg_dir] = {}

        for n_try in os.listdir(path_pkg):
            path_n_try = os.path.join(path_pkg, n_try)
            all_ui[pkg_dir][int(n_try)] = set()
            all_ssi[pkg_dir][int(n_try)] = set()

            for f in os.listdir(path_n_try):
                if f.startswith(adb_log):
                    ssi = find_ssi(os.path.join(path_n_try, f), pid=None)
                    all_ssi[pkg_dir][int(n_try)].update(ssi)

                elif f.startswith(uis_log):
                    ui = find_ui(os.path.join(path_n_try, f))
                    all_ui[pkg_dir][int(n_try)].update(ui)

                else:
                    continue




    # ----------------- #
    #   Print Results   #
    # ----------------- #
    
    print('# of SSIs before testing: %d\n' %(len(ssi_before))) 
    
    for pkg_dir in pkg_dirs:
        path_pkg = os.path.join(log_path, pkg_dir)
        if not os.path.isdir(path_pkg):
            continue
        
        cum_ui = []
        cum_ssi = []
        tries = list(all_ui[pkg_dir].keys())
        tries.sort()
        for n_try in tries:

            if n_try == 0:
                cum_ui.append(all_ui[pkg_dir][n_try])
                cum_ssi.append(all_ssi[pkg_dir][n_try])
            
            else:
                temp_ui = set()
                temp_ui.update(cum_ui[n_try-1])
                temp_ui.update(all_ui[pkg_dir][n_try])
                cum_ui.append(temp_ui)
                
                temp_ssi = set()
                temp_ssi.update(cum_ssi[n_try-1])
                temp_ssi.update(all_ssi[pkg_dir][n_try])
                cum_ssi.append(temp_ssi)

        ssi_new = set()
        ssi_new.update(cum_ssi[-1])
        for item in ssi_before:
            if item in ssi_new:
                ssi_new.remove(item)
       
        for ssi in ssi_new:
            with open('%s_ssi_except_default.log' %(pkg_dir),
                    'w', errors='ignore') as f:
                for ssi in ssi_new:
                    f.write('%s, %s, %s\n' %(ssi[0], ssi[1], ssi[2]))

 
        n_ui = [ len(n_try) for n_try in cum_ui ]
        n_ssi = [ len(n_try) for n_try in cum_ssi ]

        cdf_ui = [round((1. * ui) / n_ui[-1], 2) for ui in n_ui] \
                if n_ui[-1] != 0 else [0] * len(n_ui)
        cdf_ssi = [round((1. * ssi) / n_ssi[-1], 2) for ssi in n_ssi] \
                if n_ssi[-1] != 0 else [0] * len(n_ssi)

        
        print('\n\n%s\n - UIs: %d, SSIs: %d, new SSIs: %d' %(pkg_dir, 
            n_ui[-1], n_ssi[-1], len(ssi_new)))
        print(' - # of UIs:\n     %s' %(str(n_ui)))
        '''
        print(' - UI CDF: \n     %s\n     %s\n     %s' 
                %(str(cdf_ui[:10]), str(cdf_ui[10:20]), str(cdf_ui[20:])))
        print(' - # of SSIs:\n     %s' %(str(n_ssi)))
        print(' - SSI CDF: \n     %s\n     %s\n     %s' 
                %(str(cdf_ssi[:10]), str(cdf_ssi[10:20]), str(cdf_ssi[20:])))
        '''
    


if __name__ == '__main__':
    main()

