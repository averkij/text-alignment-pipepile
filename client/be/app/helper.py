import os
import constants as con
import pathlib
import pickle
import glob
import state_manager as state
import logging

def get_files_list(folder, mask="*.txt"):
    return [os.path.basename(x) for x in get_files_list_with_path(folder, mask)]

def get_files_list_with_path(folder, mask="*.txt"):
    if not os.path.isdir(folder):
        return []
    return glob.glob("{0}/{1}".format(folder,mask))

def get_processing_list_with_state(folder, username):
    res = []
    for file in get_files_list_with_path(folder):
        res.append({
            "name": os.path.basename(file),
            "state": state.get_processing_state(file, (con.PROC_DONE,0,0)),
            "imgs": get_files_list(os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username), mask=f"{os.path.basename(file)}.best_*.png")
            })
    return res

def create_folders(username, lang):
    if username and lang:
        pathlib.Path(os.path.join(con.STATIC_FOLDER, con.IMG_FOLDER, username)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username, con.RAW_FOLDER, lang)).mkdir(parents=True, exist_ok=True)    
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username, con.SPLITTED_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username, con.PROXY_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username, con.NGRAM_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username, con.PROCESSING_FOLDER, lang)).mkdir(parents=True, exist_ok=True)
        pathlib.Path(os.path.join(con.UPLOAD_FOLDER, username, con.DONE_FOLDER, lang)).mkdir(parents=True, exist_ok=True)

def check_folder(folder):
    pathlib.Path(folder).mkdir(parents=True, exist_ok=True) 

def check_file(folder, files, file_id):
    if len(files) < file_id+1:
        logging.debug(f"[{username}]. Document {lang} with id={file_id} not found. folder: {folder}")
        return False
    processing_file = os.path.join(folder, files[file_id])
    if not os.path.isfile(processing_file):
        logging.debug(f"[{username}]. Document {processing_file} not found.")
        return False
    return True

def get_batch(iter1, iter2, iter3, n):
    l1 = len(iter1)
    l3 = len(iter3)
    k = int(round(n * l3/l1))    
    kdx = 0 - k
    for ndx in range(0, l1, n):
        kdx += k
        yield iter1[ndx:min(ndx + n, l1)], iter2[kdx:min(kdx + k, l3)], iter3[kdx:min(kdx + k, l3)]

def get_batch_intersected(iter1, iter2, n, window):
    l1 = len(iter1)
    l2 = len(iter2)
    k = int(round(n * l2/l1))
    kdx = 0 - k

    if k<window*2:
        #subbatches will be intersected
        logging.warning(f"Batch for the second language is too small. k = {k}, window = {window}")

    for ndx in range(0, l1, n):
        kdx += k
        yield iter1[ndx:min(ndx + n, l1)], \
        iter2[max(0,kdx - window):min(kdx + k + window, l2)], \
        list(range(ndx, min(ndx + n, l1))), \
        list(range(max(0,kdx - window), min(kdx + k + window, l2)))

def get_culture(langCode):
    if langCode in CULTURE_LIST:
        return CULTURE_LIST[langCode]
    return CULTURE_LIST[DEFAULT_CULTURE]

CULTURE_LIST = {
    "en": "en-US",
    "zh": "zh-CN",
    "ru": "ru-RU",
    "de": "de-DE"
}
DEFAULT_CULTURE = "en"

def read_processing(input_file):
    docs = pickle.load(open(input_file, "rb"))
    for doc in docs:
        for line in doc:
            yield line, doc[line]["trn"], doc[line]["cnd"]

def tryParseInt(value):
    try:
        return int(value), True
    except ValueError:
        return value, False