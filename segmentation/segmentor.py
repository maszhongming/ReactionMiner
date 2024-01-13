from sentence_transformers import SentenceTransformer
import torch
import os
import json
from tqdm import tqdm
import spacy
from collections import Counter
import numpy as np

#load core english library
nlp = spacy.load("en_core_web_sm")


def cosine_sim(c1, c2):
    try:
        # works for Counter
        n1 = np.sqrt(sum([x * x for x in list(c1.values())]))
        n2 = np.sqrt(sum([x * x for x in list(c2.values())]))
        num = sum([c1[key] * c2[key] for key in c1])
    except:
        # works for ordinary list
        assert(len(c1) == len(c2))
        n1 = np.sqrt(sum([x * x for x in c1]))
        n2 = np.sqrt(sum([x * x for x in c2]))
        num = sum([c1[i] * c2[i] for i in range(len(c1))])
    try:
        if n1 * n2 < 1e-9: # divide by zero case
            return 0
        return num / (n1 * n2)
    except:
        return 0

class EnglishTokenizer:
    """
    A tokenizer is a class with tokenize(text) method
    """
    def __init__(self):
        pass

    def tokenize(self, text):
        return text.lower().split()

class C99:
    """
    Reference:
        "Advances in domain independent linear text segmentation"
    """
    def __init__(self, window=4, std_coeff=1.2, tokenizer=EnglishTokenizer()):
        """
        window: int, window size for local similarity ranking
        std_coeff: double, threshold to determine boundary, see paper for more details
        tokenizer: an object with tokenize() method,
                   which takes a string as argument and return a sequence of tokens.
        """
        self.window = window
        self.sim = None
        self.rank = None
        self.sm = None
        self.std_coeff = std_coeff
        self.tokenizer = tokenizer

    def segment(self, document):
        """
        document: list[str]
        return list[int],
            i-th element denotes whether exists a boundary right before paragraph i(0 indexed)
        """
        #assert(len(document) > 0 and len([d for d in document if not isinstance(d, str)]) == 0)
        if len(document) < 3:
            return [1] + [0 for _ in range(len(document) - 1)]
        # step 1, preprocessing
        n = len(document)
        self.window = min(self.window, n)
        
        
        #cnts = [Counter(self.tokenizer.tokenize(document[i])) for i in range(n)]
        cnts = document
        
        

        # step 2, compute similarity matrix
        self.sim = np.zeros((n, n))
        for i in range(n):
            for j in range(i, n):
                self.sim[i][j] = cosine_sim(cnts[i], cnts[j])
                self.sim[j][i] = self.sim[i][j]

        # step 3, compute rank matrix & sum matrix
        self.rank = np.zeros((n, n))
        for i in range(n):
            for j in range(i, n):
                r1 = max(0, i - self.window + 1)
                r2 = min(n - 1, i + self.window - 1)
                c1 = max(0, j - self.window + 1)
                c2 = min(n - 1, j + self.window - 1)
                sublist = self.sim[r1:(r2 + 1), c1:(c2+1)].flatten()
                lowlist = [x for x in sublist if x < self.sim[i][j]]
                self.rank[i][j] = 1.0 * len(lowlist) / ((r2 - r1 + 1) * (c2 - c1 + 1))
                self.rank[j][i] = self.rank[i][j]

        self.sm = np.zeros((n, n))
        # O(n^4) solution
        # for i in xrange(n):
        #     for j in xrange(i, n):
        #         self.sm[i][j] = sum(self.rank[i:(j + 1), i:(j + 1)].flatten())
        #         self.sm[j][i] = self.sm[i][j]
        # O(n^2) solution
        prefix_sm = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                prefix_sm[i][j] = self.rank[i][j]
                if i - 1 >= 0: prefix_sm[i][j] += prefix_sm[i - 1][j]
                if j - 1 >= 0: prefix_sm[i][j] += prefix_sm[i][j - 1]
                if i - 1 >= 0 and j - 1 >= 0: prefix_sm[i][j] -= prefix_sm[i - 1][j - 1]
        for i in range(n):
            for j in range(i, n):
                if i == 0:
                    self.sm[i][j] = prefix_sm[j][j]
                else:
                    self.sm[i][j] = prefix_sm[j][j] - prefix_sm[i - 1][j] \
                                    - prefix_sm[j][i - 1] + prefix_sm[i - 1][i - 1]
                self.sm[j][i] = self.sm[i][j]

        # step 4, determine boundaries
        D = 1.0 * self.sm[0][n - 1] / (n * n)
        darr, region_arr, idx = [D], [Region(0, n - 1, self.sm)], []
        sum_region, sum_area = float(self.sm[0][n - 1]), float(n * n)
        for i in range(n - 1):
            mx, pos = -1e9, -1
            for j, region in enumerate(region_arr):
                if region.l == region.r:
                    continue
                region.split(self.sm)
                den = sum_area - region.area + region.lch.area + region.rch.area
                cur = (sum_region - region.tot + region.lch.tot + region.rch.tot) / den
                if cur > mx:
                    mx, pos = cur, j
            assert(pos >= 0)
            tmp = region_arr[pos]
            region_arr[pos] = tmp.rch
            region_arr.insert(pos, tmp.lch)
            sum_region += tmp.lch.tot + tmp.rch.tot - tmp.tot
            sum_area += tmp.lch.area + tmp.rch.area - tmp.area
            darr.append(sum_region / sum_area)
            idx.append(tmp.best_pos)

        dgrad = [(darr[i + 1] - darr[i]) for i in range(len(darr) - 1)]

        # optional step, smooth gradient
        smooth_dgrad = [dgrad[i] for i in range(len(dgrad))]
        if len(dgrad) > 1:
            smooth_dgrad[0] = (dgrad[0] * 2 + dgrad[1]) / 3.0
            smooth_dgrad[-1] = (dgrad[-1] * 2 + dgrad[-2]) / 3.0
        for i in range(1, len(dgrad) - 1):
            smooth_dgrad[i] = (dgrad[i - 1] + 2 * dgrad[i] + dgrad[i + 1]) / 4.0
        dgrad = smooth_dgrad

        avg, stdev = np.average(dgrad), np.std(dgrad)
        cutoff = avg + self.std_coeff * stdev
        assert(len(idx) == len(dgrad))
        above_cutoff_idx = [i for i in range(len(dgrad)) if dgrad[i] >= cutoff]
        if len(above_cutoff_idx) == 0: boundary = []
        else: boundary = idx[:max(above_cutoff_idx) + 1]
        ret = [0 for _ in range(n)]
        for i in boundary:
            ret[i] = 1
            # boundary should not be too close
            for j in range(i - 1, i + 2):
                if j >= 0 and j < n and j != i and ret[j] == 1:
                    ret[i] = 0
                    break
        return [1] + ret[:-1]

class Region:
    """
    Used to denote a rectangular region of similarity matrix,
    never instantiate this class outside the package.
    """
    def __init__(self, l, r, sm_matrix):
        assert(r >= l)
        self.tot = sm_matrix[l][r]
        self.l = l
        self.r = r
        self.area = (r - l + 1)**2
        self.lch, self.rch, self.best_pos = None, None, -1

    def split(self, sm_matrix):
        if self.best_pos >= 0:
            return
        if self.l == self.r:
            self.best_pos = self.l
            return
        assert(self.r > self.l)
        mx, pos = -1e9, -1
        for i in range(self.l, self.r):
            carea = (i - self.l + 1)**2 + (self.r - i)**2
            cur = (sm_matrix[self.l][i] + sm_matrix[i + 1][self.r]) / carea
            if cur > mx:
                mx, pos = cur, i
        assert(pos >= self.l and pos < self.r)
        self.lch = Region(self.l, pos, sm_matrix)
        self.rch = Region(pos + 1, self.r, sm_matrix)
        self.best_pos = pos


class TopicSegmentor:
    def __init__(self, device='cuda:0', keywords=None):
        self.device = torch.device(device)
        # self.embedder = SentenceTransformer('bert-base-nli-stsb-mean-tokens')
        self.embedder = SentenceTransformer('allenai-specter')
        self.keywords = keywords
        self.model = C99(window = 4, std_coeff = 1)

    def init_keyword(self, sent, keyword_dict):
        for k in keyword_dict:
            if k in sent:
                return True
        return False

    def segment(self, context):
        pos = []
        sentences = []
        for c_id, sent in enumerate(context):
            doc = nlp(sent)
            sentence = []
            for s_id, s in enumerate(doc.sents):
                if self.init_keyword(str(s), self.keywords):
                    pos.append([c_id, s_id])
                sentence.append(str(s))
            sentences.append(sentence)

        ### Compute embeddings for topic tagging ###
        embeddings = []
        with torch.no_grad():
            for i in tqdm(range(0, len(sentences))):
                #tokens_input = tokenize_conv(sent[i]).cuda()
                embedding = self.embedder.encode(sentences[i])
                embeddings.append(embedding)

        ### Get the topic taggings ###
        sent_label = []
        for i in range(0, len(embeddings)):
            boundary = self.model.segment(embeddings[i])
            temp_labels = []
            l = 0
            for j in range(0, len(boundary)):
                if boundary[j] == 1:
                    l += 1
                temp_labels.append(l)
            sent_label.append(temp_labels)

        ### Align topic taggins with sentences ###
        res = []
        for item in pos:
            context = sentences[item[0]]
            topic = sent_label[item[0]]
            assert len(context) == len(topic)
            exact_topic = topic[item[1]]

            subres = []
            for t_id in range(len(topic)):
                if topic[t_id] == exact_topic:
                    subres.append(context[t_id])
            if subres not in res:
                res.append(subres)
        
        return res
    
def flat(doc):
    res = []
    for i in doc:
        if isinstance(i,dict):
            res.extend(flat(i['content']))
        else:
            res.append(i)
    return res



if __name__ == "__main__":

    segmentor = TopicSegmentor(device='cuda:0', keywords=['yields', 'yielded', 'yield', 'yielding', 'afforded', 'afford', 'affording', 'affords', 'produce', 'produces', 'produced', 'producing', "obtained"])
    
    ### load the file and flatten sentences###
    # with open('./original/Copper_Acetate.json','r') as f:
    #     sample = json.load(f)
    # context = []
    # for sec in ['introduction', 'results and discussion']:
    #     context += sample[sec] 

    # sample = []
    # with open('./original/acs_data.jsonl', 'r', encoding='utf-8') as f:
    #     for j in f.readlines():
    #         j = json.loads(j)
    #         sample.append(j)

    # ## test of nested list ##
    # context = []
    # for i in sample[1296]['full_text']:
    #     context += flat(i['content'])
    #     # if isinstance(i['content'][0], dict):
    #     #     print(i['content'])
    #     #     res = flat(i['content'])
    #     #     context += res
    #     # else:
    #     #     context += i['content']

    context = ["When 0.5 equiv of Na2S2O8 was combined with 2 equiv of Selectfluor and 20 mol % AgNO3, the reaction time decreased from 2 h to 15 min for all substrates, forming alkyl fluorides in excellent yields. The significant acceleration of rate in the decarboxylative fluorination has led to a more efficient process, suggesting that this approach may be useful for 18F labeling. In the seminal work of Li, a Ag(II) fluoride is proposed as the active fluorine atom source in the reaction as opposed to Selectfluor. To support this supposition, Li and co-workers heated the combination of tert-butyl-2-ethyltetradecaneperox-oate and Selectfluor in a sealed tube to 120 \u00b0C for 2 h. When the reaction was run in acetone, a 22% yield of 3-fluoropentadecane was obtained, whereas when the reaction was run in 50:50 acetone/water, only a 4% of fluorinated product was obtained. On the basis of these findings, Li proposed that fluorine atom transfer from Selectfluor to alkyl radicals is unlikely to be involved in the Ag-catalyzed process. Selectfluor is reported to be unstable in water at high temperature, forming HF through reaction of the reagent and water. To examine this, we heated Selectfluor in acetone-d6/D2O to 120 \u00b0C in a sealed tube for 2 h. After cooling to room temperature, a sample was removed and examined by 1H NMR, showing that 80% of the reagent decomposed to the defluorinated chloromethyl derivative (see experiment were likely not conducive to testing whether radicals can abstract a fluorine atom from Selectfluor. In addition, if a Ag(II)-F intermediate was formed during the reaction, it can be present only in a catalytic amount (at most). During its formation, radicals are also generated in a catalytic amount, so the likelihood of a small amount of radical being fluorinated by a small amount of Ag(II)-F in the presence of excess Selectfluor is unlikely. Finally, there is a large body of evidence showing that Selectfluor and similar electrophilic fluorinating reagents react with radicals to form C-F bonds.",]

    print(context)

    res = segmentor.segment(context)

    print("##### DISPLAY RESULTS #####")
    for r_id, r in enumerate(res):
        print("++++++" + str(r_id)+ "++++++")
        print(" ".join(r))
        print("\n")
