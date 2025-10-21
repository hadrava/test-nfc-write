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


app = Flask(__name__)

cfg = {
        "mdb_auth_token": os.environ.get('MDB_AUTH_TOKEN', "..."),
        }


@app.route('/api/nfc_writer/write_spool/<string:spool_unique_id>', methods=['POST'])
def write_spool(spool_unique_id):
    try:
        # Execute the command `hostname -I` to get the IP address
        data = request.get_json()
        #tag_uid = data.get('tag_uid')
        #if tag_uid is None or not tag_uid:
        #    return jsonify({'error': f'Unknown tag_uid ({tag_uid})'}), 400
        if spool_unique_id is None or not spool_unique_id:
            return jsonify({'error': f'Unknown spool_unique_id: ({spool_unique_id:})'}), 400

        print(f"Writing spool: {spool_unique_id}, (data: {data})")

    except Exception as e:
        # Return an error message if there was an exception
        print(e)
        return jsonify({'error': str(e)}), 500
    return jsonify({"status": "ok"})
