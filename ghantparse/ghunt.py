#!/usr/bin/env python3

import sys
from lib import modwall
from modules.doc import doc_hunt
from modules.gaia import gaia_hunt
from modules.youtube import youtube_hunt
import os
from pathlib import Path
from lib.utils import *
from modules.email import email_hunt

def hunt(data):
    os.chdir(Path(__file__).parents[0])
    mail = email_hunt(data)
    return mail