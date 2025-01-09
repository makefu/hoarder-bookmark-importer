# Hoarder Differential Bookmark Importer

This script performs a differential upload of the Firefox bookmarks to Hoarder by utilizing
the Hoarder API. The script will first fetch all existing bookmark URLs from Hoarder
and then diff this list against the provided file.
Every bookmark which is not yet on the server will be created, with tags and creation time added.

## Usage

1. Export your most recent Firefox bookmarks as "JSON" and put it in this folder.
2. In Hoarder, get the API key from `/settings/api-keys`.
3. `echo "ak1_random_string" > .token`
4. Also, create a new list where the bookmarks should be added to. Get the ID from `/dashboard/lists`.
5. On Nix/NixOS: run `./firefox-uploader --host https://<your-host> --list-id <your-list> bookmarks-*.json`
6. For all other operating systems: `pip install docopt requests`, then run `python3 ./firefox-uploader --host <your-host> --list-id <your-list> bookmarks-*.json`

