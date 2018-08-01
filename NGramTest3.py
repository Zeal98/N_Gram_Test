import math
import pickle
import nltk
from nltk.corpus import stopwords



class Text_Z:
    def __init__(self, text, puncs = ['.', ',', '?', '!', ':', '"']):
        self.text = text
        self.name = text[0:10]
        self.seqs = dict() #seqs[d] = dict<seq, [pos]> len(seq) = d
        self.words = list() #[sentences] sen = [words]

        self.processMark = 0 #index of current processing sentence in self.words
        
        self.counter = dict()

        self.wordslice(puncs)
        self.geneSeq(4)

    def wordslice(self, puncs): #punc:[punctuation]
        for punc in puncs:
            text = self.text.replace(punc, '.')

        sens = text.split('.')
        for sen in sens:
            temp = nltk.word_tokenize(sen)
            stops = set(stopwords.words("english"))
            temp = [word for word in temp if word not in stops]
            self.words.append(temp)

        self.text = '' #clear text to save some space

    def geneSeq(self, length): #generate seq len(seq) <= length
        for d in range(1, length+1):
            self.seqs[d] = self.seqs.get(d, dict())
        for i in range(self.processMark+1, len(self.words)):
            self.processMark = i
            for d in range(1, length+1):
                for j in range(len(self.words[i])-d):
                    seq = self.words[i][j:j+d]
                    if self.seqHash(seq) not in self.seqs[d].keys():
                        self.seqs[d][self.seqHash(seq)] = list()
                    self.seqs[d][self.seqHash(seq)].append([i, j])
                    self.counter[d] = self.counter.get(d, 0) + 1 #count total num of length d
            if i%10000 == 0:
                self.dumpTZ(self, self.name+'Temp')
                
            #print(self.counter[d])
    def dumpTZ(self, filename):
        file = open(filename, 'wb')
        pickle.dump(self, file)
        file.close()

    def loadTZ(self, filename):
        file = open(filename, 'rb')
        data = pickle.load(file)
        file.close()
        return data

    def combineTZ(self, tz):
        if self.processMark+1 < len(self.words):
            self.geneSeq(4)
        if tz.processMark+1 < len(tz.words):
            tz.geneSeq(4)

        self.text = self.text + tz.text
        self.words = self.words + tz.words
        self.processMark = len(self.words)-1
        for d in range(4):
            for key in tz.seqs[d]:
                self.seqs[d][key] = self.seqs[d].get(key, 0) + tz.seqs[d][key]
            self.counter[d] = self.counter.get(d, 0) + tz.counter.get(d, 0)
        
            

    def freqCheck(self, d, boundary): #return [seq], seq length=d, f>=boundary
        field = self.seqs[d]
        words = list()
#        count = 0
#        for poses in field.values():
#            count += len(poses)
        for seq in field:
            if len(field[seq])/self.counter[d] >= boundary:
                words.append(seq)
        print("freq check:", len(words))
        return words

    def innerCheck(self, words, boundary): #return [word] in words with higher rate of combination
        if len(words) == 0:
            return []

        result = list()

        for seq in words:
            seq = self.seqDehash(seq)
            d = len(seq)
            f = len(self.seqs[d][self.seqHash(seq)])/self.counter[d]
            temp = 0.000000001
            for s in range(d-1):
                s1 = seq[:s+1]
                s2 = seq[s+1:]
                f1 = len(self.seqs[len(s1)].get(self.seqHash(s1), []))/self.counter[len(s1)]
#                if f1>0:
#                    print(f1)
                f2 = len(self.seqs[len(s2)].get(self.seqHash(s2), []))/self.counter[len(s2)]
                temp = max(f1*f2, temp) #max predicted f suppose s1+s2 is not a combination
            #print(temp)
            if f/temp > boundary:
                result.append(self.seqHash(seq))

        print("inner check:", len(result))
        return result

    def outerCheck(self, words, boundary): #return [word] in words with more combination with other
        if len(words) == 0:
            return []
        result = list()

        for seq in words:
            seq = self.seqDehash(seq)
            d = len(seq)
            t0 = list()
            t1 = list()
            for pos in self.seqs[d][self.seqHash(seq)]:
                sen = self.words[pos[0]]
                if pos[1] > 0:
                    t0.append(sen[pos[1]-1])
                if pos[1] < len(sen) - d:
                    t1.append(sen[pos[1]+d])
            e0 = self.getInfoEntr(t0)
            e1 = self.getInfoEntr(t1)
            e = min(e0, e1)
            if e >= boundary:
                result.append(self.seqHash(seq))

        print("outer check:", len(result))
        return result

    def getInfoEntr(self, s):
        temp = dict()
        infoEntr = 0
        for entry in s:
            temp[entry] = temp.get(entry, 0) + 1
        for entry in temp:
            temp[entry] = temp[entry]/len(s)
        for entry in temp:
            infoEntr += (-temp[entry] * math.log(temp[entry]))
        return infoEntr

    def process(self, d0=2, d1=3, b1=0.0001, b2=200, b3=1.1, puncs=['.', ',', '?', '!'] ):

        seqs = list()
        for d in range(d0, d1+1):
            temp = self.freqCheck(d, b1)
            seqs = seqs + temp
        seqs = self.innerCheck(seqs, b2)
        seqs = self.outerCheck(seqs, b3)
        print("b1:", b1, "b2:", b2, "b3:", b3)
        #print(seqs)

        return seqs

    def seqHash(self, seq):
        temp = ""
        for w in seq:
            temp = temp + w + " "
        return temp[:len(temp)-1]
    def seqDehash(self, seq):
        return seq.split()

#tests

def rollTest(n, t):
    r = list()
    b1 = 0.00005
    b2 = 200
    b3 = 1.1
    r0 = t.process(2, 4, b1, b2, b3)
    r.append(r0)
    for i in range(1, 16):
        t1=b1
        t2=b2
        t3=b3
        if n==1:
            t1 = b1*(1-i/20)
        if n==2:
            t2 = b2*(1-i/20)
        if n==3:
            t3 = b3*(1-i/20)
        temp = t.process(2, 4, t1, t2, t3)
        
        r.append([word for word in temp if word not in r0])
        r0 = temp
    return r

def test():
    file = open("testtext4.txt", 'r', encoding = 'UTF-8')
    text = str()
    #for line in file:
    #    text = text + line

    t = Text_Z(file.read())
    file.close()
    
    r = rollTest(3, t)

    file = open("test_results.txt", 'w', encoding = 'UTF-8')
    for l in range(len(r)):
        print('\n', l, file = file)
        for w in r[l]:
            print(w, file = file)

    file.close()

def processArticle(ffrom, fto, n0 = 0, n1 = 1000):
    fromfile = open(ffrom, 'r')
    t = fromfile.read()
    fromfile.close()
    counter = 0
    for line in t:
        if counter in range(n0, n1):
            temp = line.split('\t')
            temp[3] = Text_Z(temp[3])
            temp[3].name = temp[0]+'\t'+temp[1]+'\t'+temp[2]
            temp[3].dumpTZ(fto)
        counter += 1
