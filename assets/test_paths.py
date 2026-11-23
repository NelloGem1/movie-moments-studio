import os
print("HOME:", os.path.expanduser("~"))
print("ASSETS:", os.path.dirname(os.path.abspath(__file__)))
print("OUT_DIR:", os.path.expanduser(r"~\Downloads\MOVIE_MOMENTS"))
