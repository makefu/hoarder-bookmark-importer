#!/usr/bin/env nix-shell
#!nix-shell -i python3 -p python3 python3Packages.requests python3Packages.docopt
"""Usage: upload.py [options] <input_file>

Options:
  --token-file=<token>  API token from hoarder [default: .token]

Arguments:
  <input_file>  JSON file (Firefox) containing bookmarks
"""

import requests
import sys
import json
from pprint import pprint
import datetime
from docopt import docopt

host = "https://bookmark.euer.krebsco.de"
# l = "pyhhs32b1ujkefvl2ld56d28" # imported bookmarks: GET /api/v1/lists
l = "d68fksyg65p1s9n4sc4bv0cp" # test
url = f"{host}/api/v1/lists/{l}"
bmarkurl=f"{url}/bookmarks"
# the bookmarks are added to the list afterwards
addbmark=f"{host}/api/v1/bookmarks"
# api/v1/lists/:listId/bookmarks/:bookmarkId
addlist=f"{bmarkurl}"
addtag=f"{addbmark}"
# url = f"{host}/api/v1/bookmarks?limit=100"


in_bookmarks = {}

def add_bookmark(node,folder_tags=None):
  if folder_tags is None:
    folder_tags = []
  bmark = {
    # collect the folder structure as tags
    "tags": set(folder_tags.copy())
  }
  for key in ["uri","title","tags""dateAdded","lastModified","id","guid"]:
    if key in node:
      bmark[key] = node[key]
  
  if "tags" in node:
    for t in node["tags"].split(","):
      bmark["tags"].add(t)

  if folder_tags and "uri" in bmark:
    for t in folder_tags:
      bmark["tags"].add(t)
  if "title" in node:
    bmark["title"] = node["title"]
  if "children" in node:
    if node["title"]:
      folder_tags.append(node["title"])
    for child in node["children"]:
      #print(node["title"])
      add_bookmark(child,folder_tags.copy())

  if "uri" in bmark:
    bmark["tags"] = list(bmark["tags"])
    in_bookmarks[bmark["uri"]] = bmark




def main():

  args = docopt(__doc__)
  infile = args['<input_file>']
  token_file = args['--token-file']
  with open(token_file) as f:
    print(f"loading token from {token_file}")
    token = f.read().strip()

  with open(infile) as f:
    print(f"loading bookmarks from file {infile}")
    add_bookmark(json.load(f))  

  #print(json.dumps(in_bookmarks))
  #sys.exit()

  headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {token}'
  }

  # query_data = json.load(open("here.json","r"))

  all_urls = {}

  def get_bookmarks(url,nextCursor=None):
    params = {
      "limit": 100
    }
    if nextCursor:
      params["cursor"] = nextCursor

    print(f"querying {url}, data: {params}")
    response = requests.request("GET", url, headers=headers, params=params)

    if response.status_code != 200:
      print(f"error: {response.status_code}, stopping")

    data = response.json()
    bookmarks = data['bookmarks']

    print(f"got data with bookmarks: {len(bookmarks)}")
    #print(data)
    for bmark in bookmarks:
        for k,v in bmark.items():
            if k == "content" and ("url" in v):
                all_urls[v["url"]] = v

    if data.get("nextCursor",None):
      get_bookmarks(url,data["nextCursor"])


  print(f"performing initial query against {bmarkurl}")
  get_bookmarks(bmarkurl)
  print(f"got a total of {len(all_urls)} urls, in_bookmarks are {len(in_bookmarks)}")

  # remove all keys from in_bookmarks which are in all_urls
  for url in list(in_bookmarks.keys()):
      if url in all_urls:
          del in_bookmarks[url]

  print(f"after removing duplicates, in_bookmarks are {len(in_bookmarks)}, now uploading all remaining bookmarks")

  for url,bmark in in_bookmarks.items():
      print(f"adding {url}")
      print(bmark)
      # ["uri","title","tags""dateAdded","lastModified","id","guid"]
      data = {
        "title": bmark["title"][:200],
        # "createdAt": int(bmark.get("dateAdded",bmark.get("lastModified",0)) / 1000),

        # "createdAt": datetime.datetime.fromtimestamp(bmark.get("dateAdded",bmark.get("lastModified",0)) / 1000000).isoformat().split("T")[0],

        "createdAt": datetime.datetime.fromtimestamp(bmark.get("dateAdded",bmark.get("lastModified",0)) / 1000000).isoformat(),
        "type": "link",
        "url": url, 
      }
      print(data)
      response = requests.request("POST", addbmark, headers=headers, json=data)
      if response.status_code not in [201]:
          print(f"error: {response.status_code}, stopping")
          print(response.text)
      ret_data = response.json()
      bmark_id = ret_data["id"]
      print(f"adding {url} to list {l}: {addlist}/{bmark_id}")
      response = requests.request("PUT", f"{addlist}/{bmark_id}", headers=headers)
      if response.status_code not in [204]:
          print(f"error: {response.status_code}, stopping")
          print(response.text)
        # import pdb; pdb.set_trace()
      
      if not bmark.get("tags",[]): 
        print(f"no tags for {bmark_id}, continuing")
        continue
          
      print(f"add tags {bmark["tags"]} to {bmark_id}: {addtag}/{bmark_id}/tags")
      tagdata = {
        "tags": [ {"tagName": s } for s in bmark["tags"]  ]
      }
      response = requests.request("POST", f"{addtag}/{bmark_id}/tags", headers=headers, json=tagdata)
      if response.status_code not in [200]:
          print(f"error: {response.status_code}, stopping")
          #import pdb; pdb.set_trace()

          print(response.text)


if __name__ == "__main__":
  main()