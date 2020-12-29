#!/usr/bin/env python
try:
    from urllib.request import urlopen
except ImportError:
    from urllib2 import urlopen

import json
import os
import multiprocessing

from bottle import route, run, response

URL_JVB_METRICS = "http://localhost:8080/colibri/stats"
BIND_IP = '0.0.0.0'
BIND_PORT = 8081


def is_skippable(key):
    skippable_keys = [
        'conference_sizes',
        'current_timestamp',
        'graceful_shutdown',
        'conferences_by_audio_senders',
        'conferences_by_video_senders',
        'version']
    return True if key in skippable_keys else False

@route("<url:re:.+>")
def iorestoacasa_exporter(url):
    """
    Gets Jvb metrics from the internal API
    and presents them in prometheus format
    """

    try:
        with urlopen(url=URL_JVB_METRICS) as f:
            data = json.loads(f.read().decode('utf-8'))

        exported_jitsi_keys = ""
        for key, value in data.items():
            if is_skippable(key):
                continue
            exported_jitsi_keys += "jitsi_{} {}\n".format(key, value)

        if 'jitsi_cpu_usage' not in exported_jitsi_keys:
            cpu_usage = float(os.popen("""top -bn 1 | grep -i '^CPU' | sed 's/%//g'  | awk '{print (100.0-$8)/100 }'""").read().strip())
            exported_jitsi_keys += "jitsi_cpu_usage {}\n".format(cpu_usage)
        exported_jitsi_keys += "jitsi_{} {}\n".format('cpu_core', multiprocessing.cpu_count())
        response.content_type = 'text/plain; charset=utf-8'
        return exported_jitsi_keys
    except Exception as e:
        return str(e)


run(host=BIND_IP, port=BIND_PORT)
