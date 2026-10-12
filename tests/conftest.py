# -*- coding: utf-8 -*-
import os
import tempfile

# Importing ittup creates the configuration folder in the user's home:
# point it to a temporary folder so tests never touch the real one
_config_home = tempfile.mkdtemp(prefix="ittup-tests-")
os.environ["HOME"] = _config_home
os.environ["LOCALAPPDATA"] = _config_home
