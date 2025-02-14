# 360 Monitoring CLI

This repository contains a CLI script for 360 Monitoring that allows you to connect to your 360 Monitoring (https://360monitoring.com) account and list monitoring data, add, update or remove server or website monitors.

## Documentation

You can find the full documentation including the feature complete REST API at [docs.360monitoring.com](https://docs.360monitoring.com/docs) and [docs.360monitoring.com/docs/api](https://docs.360monitoring.com/docs/api).

## Preconditions

 * Make sure to have an account at https://360monitoring.com or https://platform360.io

## Install 360 Monitoring CLI as ready-to-use package

    $ pip install 360monitoringcli

## Configure your account

First you need to connect your CLI to your existing 360 Monitoring account via your API KEY. If you don't have a 360 Monitoring account yet, please register for free at https://360monitoring.com. To create an API KEY you'll need to upgrade at least to a Pro plan to be able to create your API KEY.

    $ 360monitoring config save --api-key KEY     configure API KEY to connect to 360 Monitoring account

## Test 360 Monitoring CLI locally

### Test 360 Monitoring CLI with pre-configured Docker image

You can easily test and run 360 Monitoring CLI for production by running the pre-configured docker image

    $ docker build -t 360monitoringcli .
    $ docker run -it --rm 360monitoringcli /bin/bash

### Test 360 Monitoring CLI for specific staging version

 To test a package from staging you can simply deploy a docker container:

    $ docker run -it --rm ubuntu /bin/bash
    $ apt-get update && apt-get install -y python3 && apt-get install -y pip
    $ pip install -i https://test.pypi.org/simple/ --force-reinstall -v "360monitoringcli==1.0.9"

### For developement, install required Python modules

 * To test the code locally, install the Python modules "requests", "configparser", "argparse" and "prettytable"
 * Create an alias for "360monitoring=./monitoring.py"

    $ pip install requests
    $ pip install configparser
    $ pip install argparse
    $ pip install prettytable

#### Run tests to check each function works

Test the code:

    $ ./test_cli.sh

Test the deployed CLI package:

    $ ./test_cli.sh "360monitoring"
## Usage

    $ 360monitoring --help                        display general help
    $ 360monitoring config save --api-key KEY     configure API KEY to connect to 360 Monitoring account
    $ 360monitoring statistics                    display all assets of your account
    $ 360monitoring servers list                  display all monitored servers
    $ 360monitoring servers list --issues         display monitored servers with issues only
    $ 360monitoring servers list --tag cpanel     display only servers with tag "cpanel"
    $ 360monitoring sites list                    display all monitored sites
    $ 360monitoring sites list --issues           display monitored sites with issues only
    $ 360monitoring contacts list                 display all contacts
    $ 360monitoring usertokens list               display user tokens
    $ 360monitoring config print                  display your current settings and where those are stored

    $ 360monitoring sites add --url domain.tld    start monitoring a new website
    $ 360monitoring servers update --name cpanel123.hoster.com --tag production   tag a specific server

    $ 360monitoring contacts --help               display specific help for a sub command
