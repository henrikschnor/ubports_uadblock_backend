# Backend for the Ubuntu Touch app uAdBlock

This repo contains a simple server backend providing hosts files for the Ubuntu Touch app uAdBlock. Hosts files are served from the endpoint `GET /<list_combination>`, where `<list_combination>` is a string with dash-separated block list ids. Some examples are: `1`, `1-2-3`, `2-5-7-10`. Block list ids are currently hardcoded inside the app and in the `update_lists.sh` script, which prepends the id to downloaded lists in the `lists` directory. If a combination of multiple lists is requested, those lists are dynamically combined with duplicates being removed. For slightly better performance, comments are filtered out and all blocked domains are resolved to `0.0.0.0` (instead of `127.0.0.1`). The ubuntu default hosts list is prepended in each response, so that the `/etc/hosts` file can be replaced directly.

## Setup

Download/update the hosts block lists:
```
./update_lists.sh
```

Start the server:
```
./hosts_server.py
```

## Command line flags

The following optional command line flags are recognized by `hosts_server.py` (see also `./hosts_server.py --help`):

| Flag | Description |
| --- | --- |
| `-a`, `--addr` | Address for the http server to bind to |
| `-p`, `--port` | Port for the http server to listen on |
| `-d`, `--hosts-dir` | Directory containing the hosts lists. Hosts files are expected to begin with `<list_id>_`. |