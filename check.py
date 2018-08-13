from __future__ import print_function

# Tweaking
# Licenses that are known (non) FOSS that don't have valid classifiers
LICENSES = {
    'foss': ['Standard PIL License',
             'Repoze Public License',
             'BSD-derived (http://www.repoze.org/LICENSE.txt)'],
    'non_foss': [],
}
# Projects which don't have discoverable license info but are good or bad
PROJECTS = {
    'good': [],
    'bad': [],
}


# Code
import errno
from pkg_resources import Environment
import subprocess
import sys
import os

def main():
    failed = []

    print('Getting environment')
    env = Environment()

    for pkgname in env:
        print('Checking %s' % pkgname)
        if pkgname in PROJECTS['bad']:
            print('\tMarked as BAD. FAIL')
            failed.append(pkgname)
            continue
        elif pkgname in PROJECTS['good']:
            print('\tMarked as GOOD. PASS')
            continue

        for pkg in env[pkgname]:
            had_conclusive_result = False
            print('\tChecking version %s' % pkg.version)
            for check in CHECKS:
                print('\t\tRunning check: %s...' % check.__name__)
                res = check(pkg)
                if res is True:
                    print('\t\tPASS')
                    had_conclusive_result = True
                    break
                elif res is False:
                    print('\t\tFAIL')
                    had_conclusive_result = True
                    failed.append(pkg)
                    break
                elif res is None:
                    print('\t\t\tINCONCLUSIVE')
                    continue
                else:
                    print('\t\t\tINVALID RESULT: %s' % res)
                    failed.append(pkg)
                    break

            if not had_conclusive_result:
                failed.append(pkg)
                print('\t\tNO CONCLUSIVE RESULTS. FAIL')

    print()
    if failed:
        print('At least one package failed.')
        for fail in failed:
            print('\tFailure: %s' % fail)
        sys.exit(1)
    else:
        print('All packages passed license check')


def in_license_list(needle, haystack):
    needles = needle.split(' or ')
    for needle in needles:
        if needle in haystack:
            return needle
    return False


def check_license_code(liccode):
    print('\t\t\tLicense header: %s' % liccode)
    found = in_license_list(liccode, LICENSES['non_foss'])
    if found:
        print('\t\t\tNON-FOSS license: %s' % found)
        return False

    found = in_license_list(liccode, LICENSES['foss'])
    if found:
        print('\t\t\tFOSS license: %s' % found)
        return True

    print('\t\t\tUnknown license')
    return None


def try_get_metadata(pkg, *tofind):
    for option in tofind:
        if pkg.has_metadata(option):
            return pkg.get_metadata_lines(option)


# Actual license check implementations
# self-declared license in PKG-INFO metadata (from setup.py)
def check_license_from_metadata(pkg):
    pkginfo = try_get_metadata(pkg, 'PKG-INFO', 'METADATA')

    if not pkginfo:
        print('\t\t\tNo metadata found')
        return None

    had_license_classifiers = False
    liccode = None
    for line in pkginfo:
        if line.startswith('License: '):
            liccode = line[len('License: '):]
        elif line.startswith('Classifier: License :: '):
            lic = line[len('Classifier: License :: '):]
            had_license_classifiers = True
            if lic.startswith('OSI Approved :: '):
                lic = lic[len('OSI Approved :: '):]
                print('\t\t\tOSI Approved license classified: %s' % lic)
                return True
            elif lic == 'Public Domain':
                print('\t\t\tPublic Domain found')
                return True
            elif lic in LICENSES['non_foss']:
                print('\t\t\tKnown NON-FOSS license classified: %s' % lic)
                return False
            elif lic in LICENSES['foss']:
                print('\t\t\tKnown FOSS license classified: %s' % lic)
                return True
            else:
                print('\t\t\tNon-OSI Approved license classified: %s' % lic)

    if liccode:
        res = check_license_code(liccode)
        if res is not None:
            print('\t\t\tLicense result from License header: %s' % res)
            return res

    if had_license_classifiers:
        print('\t\t\tLicense classifiers found, but no OSI approved ones')
        return False

    print('\t\t\tNo license classifiers found, and header unknown')
    return None


# Check if package is from an RPM
def check_from_rpm(pkg):
    key = pkg.project_name.replace('.', '/')

    possible_dirnames = [os.path.join(pkg.location, key),
                         os.path.join(pkg.location, key)+ '.py']

    if 'path' in dir(pkg):
        possible_dirnames.append(pkg.path)

    try:
        tls = pkg.get_metadata('top_level.txt').split('\n')
        for tl in tls:
            possible_dirnames.append(os.path.join(pkg.location, tl))
            possible_dirnames.append(os.path.join(pkg.location, tl) + '.py')
    except:
        pass

    for dirname in possible_dirnames:
        if os.path.exists(dirname):
            try:
                rpmout = subprocess.check_output(['rpm', '-qf', dirname]).decode('utf8').strip()
                print('\t\t\tIn RPM (assumed acceptable): %s' % rpmout)
                return True
            except:
                print('\t\t\tError from RPM, assuming not RPM')
                return None

    print('\t\t\tUnable to find any files relating to the module, tried: %s' % ','.join(possible_dirnames))
    return None


# Define the check order
CHECKS = [check_license_from_metadata,
          check_from_rpm]


if __name__ == '__main__':
    main()
