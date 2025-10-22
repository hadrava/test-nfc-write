import socket
import subprocess
import hashlib
import json
import os
from datetime import datetime
from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
import urllib
import urllib.request
import urllib.error
import traceback

from .nfc_writer import NFCWriter
from .filaweb_api import FilawebAPI
from .tag_create import TagCreator

app = Flask(__name__)

cfg = {
        "mdb_auth_token": os.environ.get('MDB_AUTH_TOKEN', "..."),
        "filaweb_ws_url": os.environ.get('FILAWEB_WS_URL', "http://filaweb.prusa/ws/ws.php"),
        "nfc_writer_socket_path": os.environ.get('NFC_WRITER_SOCKET_PATH', "/tmp/nfc_writer_socket.sock"),
        "mdb_path": os.environ.get('MDB_PATH', "mdb_data.json"),
        }


filaweb_client = FilawebAPI(cfg['filaweb_ws_url'])
nfc_writer_client = NFCWriter(cfg['nfc_writer_socket_path'])
tag_creator = TagCreator(cfg['mdb_path'])

@app.route('/api/nfc_writer/write_spool/<string:spool_unique_id>', methods=['POST'])
def write_spool(spool_unique_id):
    try:
        # Execute the command `hostname -I` to get the IP address
        data = request.get_json()
        #tag_uid = data.get('tag_uid')
        #if tag_uid is None or not tag_uid:
        #    return jsonify({'error': f'Unknown tag_uid ({tag_uid})'}), 400
        if spool_unique_id is None or not spool_unique_id:
            return jsonify({'error': f'Unknown spool_unique_id: ({spool_unique_id})'}), 400

        print(f"I would like to write on spool: {spool_unique_id}, (data: {data})")
        info = filaweb_client.get_spool_info(spool_unique_id)
        print(f"spool_info: {info}")
        tag_content = tag_creator.create_tag(info)
        print(f"tag_content: {tag_content}")
        response = nfc_writer_client.write_tag(info.tag_uid, tag_content)

        code = 400
        if response.get('status') == "ok":
            code = 200
        return jsonify(response), code

    except Exception as e:
        # Return an error message if there was an exception
        print(e)
        return jsonify({'error': str(e)}), 500
    return jsonify({"status": "ok"})
