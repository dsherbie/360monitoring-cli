#!/usr/bin/env python3

import requests
import json
from prettytable import PrettyTable

from .config import Config
from .functions import printError, printWarn
from .bcolors import bcolors

class Servers(object):

    def __init__(self, config):
        self.config = config
        self.servers = None
        self.format = 'table'
        self.table = PrettyTable()
        self.table.field_names = ['ID', 'Server name', 'IP Address', 'Status', 'OS', 'CPU Usage %', 'Mem Usage %', 'Disk Usage %', 'Disk Info', 'Tags']
        self.table.align['ID'] = 'l'
        self.table.align['Server name'] = 'l'
        self.table.align['Tags'] = 'l'

        self.sum_cpu_usage = 0
        self.sum_mem_usage = 0
        self.sum_disk_usage = 0
        self.num_servers = 0

    def fetchData(self):
        """Retrieve a list of all monitored servers"""

        # if data is already downloaded, use cached data
        if self.servers != None:
            return True

        # check if headers are correctly set for authorization
        if not self.config.headers():
            return False

        if self.config.debug:
            print('GET', self.config.endpoint + 'servers?', self.config.params())

        # Make request to API endpoint
        response = requests.get(self.config.endpoint + 'servers', params=self.config.params(), headers=self.config.headers())

        # Check status code of response
        if response.status_code == 200:
            # Get list of servers from response
            self.servers = response.json()['servers']
            return True
        else:
            printError('An error occurred:', response.status_code)
            self.servers = None
            return False

    def update(self, serverId: str, tags):
        """Update a specific server and add specified tags to it"""

        data = {
            "tags": tags
        }

        if self.config.debug:
            print('PUT', self.config.endpoint + 'server/' + serverId + '?', data)

        if self.config.readonly:
            return False

        # Make request to API endpoint
        response = requests.put(self.config.endpoint + 'server/' + serverId,  data=json.dumps(data), headers=self.config.headers())

        # Check status code of response
        if response.status_code == 200:
            print('Updated tags of server', serverId, 'to', tags)
            return True
        else:
            printError('Failed to update server', serverId, 'with response code:', response.status_code)
            return False

    def list(self, issuesOnly: bool, tags):
        """Iterate through list of server monitors and print details"""

        if self.fetchData():
            self.printHeader()

            # Iterate through list of monitors and print urls, etc.
            for server in self.servers:
                if len(tags) == 0:
                    if (not issuesOnly) or self.hasIssue(server):
                        self.print(server)
                elif 'tags' in server:
                    match = True
                    for tag in tags:
                        if not tag in server['tags']:
                            match = False
                            break
                    if match:
                        if (not issuesOnly) or self.hasIssue(server):
                            self.print(server)

            self.printFooter()

    def setTags(self, pattern: str, tags):
        """Set the tags for the server specified with pattern. Pattern can be either the server ID or its name"""

        if pattern and len(tags) > 0 and self.fetchData():
            for server in self.servers:
                if pattern == server['id'] or pattern in server['name']:
                    return self.update(server['id'], tags)

        printWarn('No server with given pattern found: ' + pattern)

    def hasIssue(self, server):
        """Return True if the specified server has some issue by having a value outside of the expected threshold specified in config file"""

        cpu_usage_percent = server['summary']['cpu_usage_percent'] if 'summary' in server else 0
        mem_usage_percent = server['summary']['mem_usage_percent'] if 'summary' in server else 0
        disk_usage_percent = server['summary']['disk_usage_percent'] if 'summary' in server else 0

        if cpu_usage_percent >= float(self.config.threshold_cpu_usage) \
            or mem_usage_percent >= float(self.config.threshold_mem_usage) \
            or disk_usage_percent >= float(self.config.threshold_disk_usage):
            return True

        last_data = server['last_data']
        if 'df' in last_data:
            for disk in last_data['df']:
                free_disk_space = disk['free_bytes']
                used_disk_space = disk['used_bytes']
                total_disk_space = free_disk_space + used_disk_space
                free_disk_space_percent = free_disk_space / total_disk_space * 100

                if free_disk_space_percent <= float(self.config.threshold_free_diskspace):
                    return True

        return False

    def printHeader(self):
        """Print CSV if CSV format requested"""

        if (self.format == 'csv'):
            print('id;server name;ip address;status;os;cpu usage %;mem usage %;disk usage %;free disk space;tags')

        self.sum_cpu_usage = 0
        self.sum_mem_usage = 0
        self.sum_disk_usage = 0
        self.num_servers = 0

    def printFooter(self):
        """Print table if table format requested"""

        if (self.format == 'table'):

            avg_cpu_usage = self.sum_cpu_usage / self.num_servers if self.sum_cpu_usage > 0 and self.num_servers > 0 else 0
            avg_mem_usage = self.sum_mem_usage / self.num_servers if self.sum_mem_usage > 0 and self.num_servers > 0 else 0
            avg_disk_usage = self.sum_disk_usage / self.num_servers if self.sum_disk_usage > 0 and self.num_servers > 0 else 0

            if avg_cpu_usage >= float(self.config.threshold_cpu_usage):
                avg_cpu_usage_text = f"{bcolors.FAIL}" + "{:.1f}".format(avg_cpu_usage) + '%' + f"{bcolors.ENDC}"
            else:
               avg_cpu_usage_text = "{:.1f}".format(avg_cpu_usage) + '%'

            if avg_mem_usage >= float(self.config.threshold_mem_usage):
                avg_mem_usage_text = f"{bcolors.FAIL}" + "{:.1f}".format(avg_mem_usage) + '%' + f"{bcolors.ENDC}"
            else:
               avg_mem_usage_text = "{:.1f}".format(avg_mem_usage) + '%'

            if avg_disk_usage >= float(self.config.threshold_disk_usage):
                avg_disk_usage_text = f"{bcolors.FAIL}" + "{:.1f}".format(avg_disk_usage) + '%' + f"{bcolors.ENDC}"
            else:
               avg_disk_usage_text = "{:.1f}".format(avg_disk_usage) + '%'

            # add average row as table footer
            self.table.add_row(['', 'Average of ' + str(self.num_servers) + ' servers', '', '', '', avg_cpu_usage_text, avg_mem_usage_text, avg_disk_usage_text, '', ''])

            if self.config.hide_ids:
                self.table.del_column('ID')

            # Get string to be printed and create list of elements separated by \n
            list_of_table_lines = self.table.get_string().split('\n')

            # Use the first line (+---+-- ...) as horizontal rule to insert later
            horizontal_line = list_of_table_lines[0]

            # Print the table
            # Treat the last n lines as "result lines" that are seperated from the
            # rest of the table by the horizontal line
            result_lines = 1
            print("\n".join(list_of_table_lines[:-(result_lines + 1)]))
            print(horizontal_line)
            print("\n".join(list_of_table_lines[-(result_lines + 1):]))

    def print(self, server):
        """Print the data of the specified server monitor"""

        if (self.format == 'json'):
            print(json.dumps(server, indent=4))
            return

        id = server['id']
        name = server['name']
        os = server['os'] if 'os' in server else ''
        agent_version = server['agent_version'] if 'agent_version' in server else ''
        status = server['status'] if 'status' in server else ''
        last_data = server['last_data']
        uptime_seconds = last_data['uptime']['seconds'] if 'uptime' in last_data else 0
        cores = last_data['cores'] if 'cores' in last_data else 0
        memory_used = last_data['memory']['used'] if 'memory' in last_data else 0
        memory_free = last_data['memory']['free'] if 'memory' in last_data else 0
        memory_available = last_data['memory']['available'] if 'memory' in last_data else 0
        memory_total = last_data['memory']['total'] if 'memory' in last_data else 0
        connecting_ip = server['connecting_ip'] if 'connecting_ip' in server else ''
        if 'ip_whois' in server:
            ip_whois = server['ip_whois']
            ip_address = ip_whois['ip'] if 'ip' in ip_whois else ''
            ip_country = ip_whois['country'] if 'country' in ip_whois else ''
            ip_hoster = ip_whois['org'] if 'org' in ip_whois else ''
        else:
            ip_address = ''
            ip_country = ''
            ip_hoster = ''
        cpu_usage_percent = server['summary']['cpu_usage_percent'] if 'summary' in server else 0
        mem_usage_percent = server['summary']['mem_usage_percent'] if 'summary' in server else 0
        disk_usage_percent = server['summary']['disk_usage_percent'] if 'summary' in server else 0

        self.sum_cpu_usage = self.sum_cpu_usage + cpu_usage_percent
        self.sum_mem_usage = self.sum_mem_usage + mem_usage_percent
        self.sum_disk_usage = self.sum_disk_usage + disk_usage_percent
        self.num_servers = self.num_servers + 1

        if cpu_usage_percent >= float(self.config.threshold_cpu_usage):
            cpu_usage_percent_text = f"{bcolors.FAIL}" + "{:.1f}".format(cpu_usage_percent) + '%' + f"{bcolors.ENDC}"
        else:
            cpu_usage_percent_text = "{:.1f}".format(cpu_usage_percent) + '%'

        if mem_usage_percent >= float(self.config.threshold_mem_usage):
            mem_usage_percent_text = f"{bcolors.FAIL}" + "{:.1f}".format(mem_usage_percent) + '%' + f"{bcolors.ENDC}"
        else:
            mem_usage_percent_text = "{:.1f}".format(mem_usage_percent) + '%'

        if disk_usage_percent >= float(self.config.threshold_disk_usage):
            disk_usage_percent_text = f"{bcolors.FAIL}" + "{:.1f}".format(disk_usage_percent) + '%' + f"{bcolors.ENDC}"
        else:
            disk_usage_percent_text = "{:.1f}".format(disk_usage_percent) + '%'

        tags = ''
        if 'tags' in server:
            for tag in server['tags']:
                if tags:
                    tags += ', ' + tag
                else:
                    tags = tag

        disk_info = ''
        if 'df' in last_data:
            for disk in last_data['df']:
                free_disk_space = disk['free_bytes']
                used_disk_space = disk['used_bytes']
                total_disk_space = free_disk_space + used_disk_space
                free_disk_space_percent = free_disk_space / total_disk_space * 100
                mount = disk['mount']

                # add separator
                if disk_info:
                    disk_info += ', '

                if free_disk_space_percent <= float(self.config.threshold_free_diskspace):
                    disk_info += f"{bcolors.FAIL}" + "{:.0f}".format(free_disk_space_percent) + "% free on " + mount + f"{bcolors.ENDC}"
                else:
                    disk_info += "{:.0f}".format(free_disk_space_percent) + "% free on " + mount

        if (self.format == 'csv'):
            print(f"{id};{name};{ip_address};{status};{os};{cpu_usage_percent};{mem_usage_percent};{disk_usage_percent};{disk_info};{tags}")
        else:
            self.table.add_row([id, name, ip_address, status, os, cpu_usage_percent_text, mem_usage_percent_text, disk_usage_percent_text, disk_info, tags])
