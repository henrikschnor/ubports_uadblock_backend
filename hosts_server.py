#!/usr/bin/env python3

import argparse
import functools
import logging
import os
import re
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


# Domains that are not indended to be blocked
# and which will be filtered out from block lists.
# Some of these are contained in the original OS hosts list,
# which is prepended to the generated block list.
NO_BLOCK_DOMAINS = [
    'localhost',
    'localhost.localdomain',
    'local',
    '0.0.0.0'
]

# Number of concurrent connections we can handle
HTTP_SERVER_THREADS = 10
# Number of connections to additionally keep
# in the queue without disconnecting clients
HTTP_SERVER_QUEUE = 5


class HostsRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, default_hosts, hosts_lists, *args, **kwargs):
        self.default_hosts = default_hosts
        self.hosts_lists = hosts_lists
        super().__init__(*args, **kwargs)

    def do_GET(self):
        try:
            # Check if the endpoint looks like a valid list combination
            if not re.fullmatch(r'/[0-9]+(?:-[0-9]+)*', self.path):
                logging.warning(f'Invalid request to endpoint: {self.path}')
                self.send_error(404, 'invalid identifier')
                return
            # Get the host list ids
            list_ids = set([int(id) for id in self.path[1:].split('-')])
            # Make sure we have all those lists loaded
            for id in list_ids:
                if id not in self.hosts_lists:
                    logging.warning(f'Invalid list id {id} in request: {self.path}')
                    self.send_error(404, f'invalid list id: {id}')
                    return
            # We're confident we can handle this request,
            # so let's send the default hosts list to give
            # the client some first breadcrumbs
            logging.info(f'Handling request: {self.path}')
            self.send_response(200)
            self.send_header('Content-type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(self.default_hosts.encode())
            # Generate the block list and send it
            time_start = time.time()
            block_list = combine_lists(self.hosts_lists, list_ids)
            time_end = time.time()
            time_diff = int((time_end - time_start) * 1000)
            logging.debug(f'Blocklist generation took {time_diff} ms')
            self.wfile.write(block_list.encode())
        except (ConnectionResetError, BrokenPipeError) as err:
            logging.info(str(err))
    
    def log_message(self, format, *args):
        logging.info(self.address_string() + ' - ' + format % args)

def http_server_thread(thread_id, addr, sock, default_hosts, hosts_lists):
    logging.info(f'Starting http server thread {thread_id+1}...')
    request_handler = functools.partial(HostsRequestHandler, default_hosts, hosts_lists)
    httpd = HTTPServer(addr, request_handler, False)
    # Prevent the HTTP server from re-binding every handler.
    # https://stackoverflow.com/questions/46210672/
    httpd.socket = sock
    httpd.server_bind = lambda self: None
    httpd.serve_forever()

def start_http_server(addr, port, default_hosts, hosts_lists):
    logging.info(f'Starting http server on {addr}:{port}...')
    # Create a single socket
    sock = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((addr, port))
    sock.listen(HTTP_SERVER_QUEUE)
    # Start n-1 http handler threads
    for thread_idx in range(HTTP_SERVER_THREADS-1):
        thread_args = (thread_idx, addr, sock, default_hosts, hosts_lists)
        threading.Thread(target=http_server_thread, args=thread_args, daemon=True).start()
    # The last http handler will run in the current thread
    http_server_thread(HTTP_SERVER_THREADS-1, addr, sock, default_hosts, hosts_lists)


def load_hosts_domains(file_path):
    # Read all blocked domains from a hosts file
    with open(file_path, 'r') as f:
        block_domains = set()
        # Read the file line by line
        for line in f.readlines():
            # Rules start with one of two IPs they resolve blocked domains to
            if not (line.startswith('127.0.0.1 ') or line.startswith('0.0.0.0 ')):
                continue
            # The domain name starts somewhere after the IP...
            domain_idx_start = line.index(' ') + 1
            # ...and ends before an optional comment or at line end.
            domain_idx_end = line.index('#') if '#' in line else len(line)
            domain = line[domain_idx_start:domain_idx_end].strip()
            # Some block lists include rules for localhost, etc.
            # We don't need those.
            if domain in NO_BLOCK_DOMAINS:
                continue
            block_domains.add(domain)
        return block_domains

def combine_lists(hosts_lists, list_ids):
    # Combine the domains from all chosen block lists
    domains = set()
    for list_id in list_ids:
        domains.update(hosts_lists[list_id])
    # Generate the block list in a plain text string
    combination_id = '-'.join(sorted(map(str, list_ids)))
    prefix = f'# uAdBlock generated block list ({combination_id})\n0.0.0.0 '
    return prefix + '\n0.0.0.0 '.join(sorted(domains)) + '\n'

def main():
    # Parse arguments
    arg_parser = argparse.ArgumentParser(description='Serves hosts files for uAdBlock')
    arg_parser.add_argument('-a', '--addr', action='store', default='0.0.0.0', help='Address to bind to')
    arg_parser.add_argument('-p', '--port', action='store', default=8080, type=int, help='Port to bind to')
    arg_parser.add_argument('-d', '--hosts-dir', action='store', default='lists', help='Directory containing the hosts lists')
    args = arg_parser.parse_args()
    # Configure logging
    logging.basicConfig(format='%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s', level=logging.DEBUG)
    logging.info('Starting...')
    # Load default hosts file (this will be prepended to generated lists)
    logging.info('Loading default hosts...')
    with open('hosts.01-ubuntu-default', 'r') as f:
        ubuntu_default_hosts = f.read()
    # Block files should be placed in the lists directory
    if not os.path.isdir(args.hosts_dir):
        logging.error(f'Lists directory "{args.hosts_dir}" doesn\'t exist. Path correct? Maybe run update_lists.sh first.')
        sys.exit(1)
    # Load all domains from the individual hosts files
    hosts_lists = {}
    for hosts_file in sorted(os.listdir(args.hosts_dir)):
        hosts_file_path = os.path.join(args.hosts_dir, hosts_file)
        # Each file name should start with <list_id>_
        file_match = re.match(r'([0-9]+)_', hosts_file)
        if os.path.isfile(hosts_file_path) and file_match:
            logging.info(f'Loading block list: {hosts_file_path}')
            list_id = int(file_match.group(1))
            list_domains = load_hosts_domains(hosts_file_path)
            hosts_lists[list_id] = list_domains
    # Start the http server (blocks forever)
    start_http_server(args.addr, args.port, ubuntu_default_hosts, hosts_lists)

if __name__ == '__main__':
    main()