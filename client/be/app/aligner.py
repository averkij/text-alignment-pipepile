import pickle
from typing import List

import numpy as np
from scipy import spatial

import config
import helper
import model_dispatcher


def serialize_docs(lines_ru, lines_zh, processing_ru, threshold=config.DEFAULT_TRESHOLD, batch_size=config.DEFAULT_BATCHSIZE):
    batch_number = 1
    docs = []
    vectors1 = []
    vectors2 = []
    
    for lines_ru_batch, lines_ru_proxy_batch, lines_zh_batch in helper.get_batch(lines_ru, lines_zh, lines_zh, batch_size):
        print("batch:", batch_number)
        vectors1 = [*vectors1, *get_line_vectors(lines_zh_batch)]
        vectors2 = [*vectors2, *get_line_vectors(lines_ru_batch)]
        batch_number += 1

        #test version restriction
        break

    sim_matrix = get_sim_matrix(vectors1, vectors2)
    # res_ru, res_zh, res_ru_proxy, sims = get_pairs(lines_ru, lines_zh, lines_zh, sim_matrix, threshold)
    
    doc = get_processed(lines_ru, lines_zh, sim_matrix, threshold, batch_number, batch_size)
    docs.append(doc)
        
    pickle.dump(docs, open(processing_ru, "wb"))

def get_line_vectors(lines):
    return model_dispatcher.models[config.MODEL].embed(lines)

def get_processed(ru_lines, zh_lines, sim_matrix, threshold, batch_number, batch_size, candidates_count=5):
    doc = {}
    for ru_line_id in range(sim_matrix.shape[1]):
        line = DocLine([ru_line_id], ru_lines[ru_line_id])
        doc[line] = []
        zh_candidates = []
        for zh_line_id in range(sim_matrix.shape[0]):            
            if sim_matrix[zh_line_id,ru_line_id] > 0 and sim_matrix[zh_line_id,ru_line_id] >= threshold:
                zh_candidates.append((zh_line_id, sim_matrix[zh_line_id,ru_line_id]))
        for i,c in enumerate(sorted(zh_candidates, key=lambda x: x[1], reverse=True)[:candidates_count]):
            doc[line].append((DocLine([c[0]], zh_lines[c[0]]), sim_matrix[c[0], ru_line_id], 1 if i==0 else 0))
    return doc

def get_pairs(ru_lines, zh_lines, ru_proxy_lines, sim_matrix, threshold):
    ru = []
    zh = []
    ru_proxy = []
    sims = []
    for i in range(sim_matrix.shape[0]):
        for j in range(sim_matrix.shape[1]):
            if sim_matrix[i,j] >= threshold:
                ru.append(ru_lines[j])
                zh.append(zh_lines[i])
                ru_proxy.append(ru_proxy_lines[i])
                sims.append(sim_matrix[i,j])
                
    return ru,zh,ru_proxy,sims

def get_sim_matrix(vec1, vec2, window=config.DEFAULT_WINDOW):
    sim_matrix = np.zeros((len(vec1), len(vec2)))
    k = len(vec1)/len(vec2)
    for i in range(len(vec1)):
        for j in range(len(vec2)):
            if (j*k > i-window) & (j*k < i+window):
                sim = 1 - spatial.distance.cosine(vec1[i], vec2[j])
                sim_matrix[i,j] = sim
    return sim_matrix

class DocLine:
    def __init__(self, line_ids:List, text=None):
        self.line_ids = line_ids
        self.text = text
    def __hash__(self):
        return hash(self.text)
    def __eq__(self, other):
        return self.text == other
    def isNgramed(self) -> bool:
        return len(self.line_ids)>1
