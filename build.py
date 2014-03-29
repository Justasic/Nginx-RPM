#!/bin/env python
# 
# I built this script because spectool is an epic failure and so is rpmbuild.
# GitHub downloads things via Content-Disposition which means that the download
# file differs from the one given in the url.
# This makes rpmbuild freak the fuck out because it cant find the file. This could
# be easy to solve if I could simply tell rpmbuild "Download from this URL but the file
# is actually gonna be named this".
#
# In any case, this script will download the needed files for nginx and then run rpmbuild.
# It will also check for the fedora-packager and various libs needed to build nginx with
# pagespeed. This will drastically easy the compile of nginx.

import os, sys
from subprocess import call

try:
	import yum
except:
	print "Please install the yum python api to use this script."
	sys.exit(1)

try:
	import platform
	hasplatform = True
except:
	print "[WARNING] cannot import python-platform, gperftools-devel may be a required package!"
	hasplatform = False

NGINXVER = "1.5.12"
PAGESPEEDVER = "1.7.30.4"

# List of all the packages we need.
PACKAGES = [
	"fedora-packager",
	"GeoIP-devel",
	"gd-devel",
	"libxslt-devel",
	"openssl-devel",
	"pcre-devel",
	"perl-devel",
	"zlib-devel",
	"pam-devel",
	"GeoIP",
	"gd",
	"openssl",
	"pcre",
	"shadow-utils",
	"gcc-c++",
	"perl-ExtUtils-Embed",
]

URLS = [
	"http://nginx.org/download/nginx-%s.tar.gz" % NGINXVER,
	"http://nginx.org/download/nginx-%s.tar.gz.asc" % NGINXVER,
	"https://github.com/pagespeed/ngx_pagespeed/archive/v%s-beta.tar.gz" % PAGESPEEDVER,
	"https://dl.google.com/dl/page-speed/psol/%s.tar.gz" % PAGESPEEDVER,
	"https://github.com/gnosek/nginx-upstream-fair/archive/master.tar.gz",
	"https://github.com/masterzen/nginx-upload-progress-module/archive/v0.9.0.tar.gz",
	"https://github.com/vkholodkov/nginx-upload-module/archive/2.2.0.tar.gz",
	"https://github.com/arut/nginx-rtmp-module/archive/v1.0.3.tar.gz",
	"https://github.com/evanmiller/mod_zip/archive/master.tar.gz",
	"http://web.iti.upv.es/~sto/nginx/ngx_http_auth_pam_module-1.2.tar.gz",
]

LOCATION = os.path.expanduser("~/rpmbuild/SOURCES/")

def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes":True,   "y":True,  "ye":True,
             "no":False,     "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "\
                             "(or 'y' or 'n').\n")

def which(program):
	def is_exe(fpath):
		return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

	fpath, fname = os.path.split(program)
	if fpath:
		if is_exe(program):
			return program
	else:
		for path in os.environ["PATH"].split(os.pathsep):
			path = path.strip('"')
			exe_file = os.path.join(path, program)
			if is_exe(exe_file):
				return exe_file

	return None


def CheckPackages():
	global PACKAGES
	if not which("yum"):
		print "Yum is not in PATH or not found? cannot continue."
		sys.exit(1)

	if not which("wget"):
		PACKAGES += ["wget"]

	hassudo = which("sudo")
	needsudo = False
	if (not hassudo) and (os.getuid() == 0):
		needsudo = False
	else:
		if not hassudo:
			print "You do not have the sudo command, please install it or run this script as root."
		needsudo = True

	yb = yum.YumBase()
	needpackages = False
	for p in PACKAGES:
		if yb.rpmdb.searchNevra(name=p):
			needpackages = True
			print "Don't have package '%s'" % p
			break

	if needpackages:
		ans = query_yes_no("Some packages are not installed on this system, would you like me to install them? (This may ask for your sudo password)")
		if ans:
			if needsudo:
				command = ["sudo", "yum", "-y", "install"] + PACKAGES
			else:
				command = ["yum", "-y", "install"] + PACKAGES

			p1 = call(command)
			if p1 != 0:
				print "There was some kind of error (see yum output above)\nRan the following yum command:\nyum install %s" % " ".join(PACKAGES)
		else:
			print "User said no, skipping..."

def wget(url):
	global LOCATION
	command = ["wget", "--content-disposition", "-N", "--retr-symlinks", "-P", LOCATION, url]
	ec = call(command)
	if ec != 0:
		print "There was some kind of error. Please review and fix. Command was:\n%s\n" % " ".join(command)
		sys.exit(1)

def DownloadSources():
	global URLS
	for u in URLS:
		wget(u)


def CompilePackage():
	path = os.path.expanduser("~/rpmbuild/nginx.spec")
	exitcode = call(["rpmbuild", "-ba", path])
	if exitcode != 0:
		print "rpmbuild command failed. Command was:\nrpmbuild -ba %s" % path
		sys.exit(1)

if __name__ == "__main__":

	# First we need to find our architecture
	if hasplatform:
		arch = platform.machine()
		# There's other platforms needed like ix86 and arm* but too lazy.
		if arch in ["ppc", "ppc64", "x86_64"]:
			PACKAGES += ["gperftools-devel"]
	
	CheckPackages()
	DownloadSources()
	CompilePackage()
	
	

