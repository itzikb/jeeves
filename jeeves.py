#!/usr/bin/env python

import os
import sys
import yaml
import jenkins
import argparse

from jeeves.report import run_report
from jeeves.remind import run_remind
from jeeves.common import generate_header, validate_config

os.environ['PYTHONHTTPSVERIFY'] = '0'


if __name__ == '__main__':

	# initialize argument parser
	parser = argparse.ArgumentParser(description='An automated report generator for Jenkins CI')

	# set customization flags
	parser.add_argument("--config", default="config.yaml", type=str, help='Configuration YAML file to use')
	parser.add_argument("--blockers", default="blockers.yaml", type=str, help='Blockers YAML file to use')
	parser.add_argument("--preamble", default=False, type=str, help='Preamble HTML file to use')
	parser.add_argument("--template", default="report_template.html", type=str, help='Template HTML file to use (must be in "templates" directory)')

	# set configuration flags
	parser.add_argument("--mode", default="report", type=str, choices=['report', 'remind'], help='Flag to specify which mode to run Jeeves in')
	parser.add_argument("--no-email", default=False, action='store_true', help='Flag to not send an email of the report')
	parser.add_argument("--test-email", default=False, action='store_true', help='Flag to send email to test email address')

	# parse arguments
	args = parser.parse_args()
	config_file = args.config
	blocker_file = args.blockers
	preamble_file = args.preamble
	template_file = args.template
	mode = args.mode
	no_email = args.no_email
	test_email = args.test_email

	# load configuration data - if YAML format is invalid, log and end program execution
	try:
		with open(config_file, 'r') as file:
			config = yaml.safe_load(file)
			validate_config(config, no_email, test_email)
	except Exception as e:
		print("Error loading configuration data: ", e)
		sys.exit(1)

	# load blocker data - if YAML format is invalid, log and end program execution
	try:
		with open(blocker_file, 'r') as file:
			blockers = yaml.safe_load(file)
	except Exception as e:
		print("Error loading blocker configuration data: ", e)
		sys.exit(1)

	# connect to jenkins server - if not possible, log and end program execution
	try:
		server = jenkins.Jenkins(config['jenkins_url'])
	except Exception as e:
		print("Error connecting to Jenkins server: ", e)
		sys.exit(1)

	# fetch optional config options, return None if not present
	fpn = config.get('filter_param_name', None)
	fpv = config.get('filter_param_value', None)

	# generate header and execute Jeeves in either 'remind' or 'report' mode
	# if remind, header source should be blocker_file
	# if report, header source should be job_search_fields
	if mode == 'report':
		header = generate_header(config['job_search_fields'], filter_param_name=fpn, filter_param_value=fpv)
		run_report(config, blockers, preamble_file, template_file, no_email, test_email, server, header)
	elif mode == 'remind':
		header = generate_header(blocker_file, filter_param_name=fpn, filter_param_value=fpv, remind=True)
		run_remind(config, blockers, server, header)
	else:
		print("Invalid mode selected: ", mode)
		sys.exit(1)
