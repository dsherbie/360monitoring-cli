#!/usr/bin/env python3

import requests
import json
from prettytable import PrettyTable
from lib.monitoringconfig import MonitoringConfig

class Servers(object):

    def __init__(self, config):
        self.config = config
        self.format = 'table'
        self.table = PrettyTable()
        self.table.field_names = ["Server name", "OS", "Disk Info"]
        self.servers = None

    def fetch_data(self):
        """Retrieve a list of all monitored servers"""

        if self.servers != None:
            return True

        # Make request to API endpoint
        response = requests.get(self.config.endpoint + "servers", params="perpage=" + str(self.config.max_items), headers=self.config.headers())

        # Check status code of response
        if response.status_code == 200:
            # Get list of servers from response
            self.servers = response.json()["servers"]
            return True
        else:
            print("An error occurred:", response.status_code)
            self.servers = None
            return False

    def list(self):
        """Iterate through list of server monitors and print details"""

        self.fetch_data()
        self.print_header()

        # Iterate through list of monitors and print urls, etc.
        for server in self.servers:
            self.print(server)

        self.print_footer()

    def get(self, pattern: str):
        """Print the data of all server monitors that match the specified server name"""

        if pattern:
            self.fetch_data()

            for server in self.servers:
                if pattern == server["id"] or pattern in server["name"]:
                    self.print(server)

    def print_header(self):
        """Print CSV if CSV format requested"""
        if (self.format == 'csv'):
            print('name;os;free disk space')

    def print_footer(self):
        """Print table if table format requested"""
        if (self.format == 'table'):
            print(self.table)

    def print(self, server):
        """Print the data of the specified server monitor"""

        name = server["name"]
        os = server["os"]
        last_data = server["last_data"]
        disk_info = ""
        for disk in last_data["df"]:
            free_disk_space = disk["free_bytes"]
            used_disk_space = disk["used_bytes"]
            total_disk_space = free_disk_space + used_disk_space
            free_disk_space_percent = free_disk_space / total_disk_space * 100
            mount = disk["mount"]
            if disk_info:
                disk_info += ", {:.0f}".format(free_disk_space_percent) + "% free on " + mount
            else:
                disk_info += "{:.0f}".format(free_disk_space_percent) + "% free on " + mount

        if (self.format == 'table'):
            self.table.add_row([name, os, disk_info])

        elif (self.format == 'csv'):
            print(f"{name};{os};{disk_info}")

        else:
            print(json.dumps(server, indent=4))
