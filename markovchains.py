#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re
import random
import sys

from util import *

class MarkovChains(object):
    def __init__(self, order_num=3):
        self.num = order_num
        self.chaindic = {}
        self.userchaindic = {}

    def _get_punctuation(self):
        punctuation_words = {
		u'。': 0,
		u'．': 0,
		u'.': 0,
		u'？': 0,
		u'！': 0,
		u'!': 0,
		u'?': 0,
		u'…': 0}
        return punctuation_words

    def analyze_sentence(self, _text, user=None):
        text = _text
	#regulation : japanese space
        text = text.replace(u'　', u' ')
	#regulation : sentence fitting i.e. "a. a."-> "a.a."
        for word in self._get_punctuation():
            text = re.sub(u'(\%s)\s+' % (word), word, text)
        sentences = self._split_sentences(text)
	for sentence in sentences:
		words = self._get_words(sentence)
		self._update_newchains_ins(words)
		if user:
			self._update_newchains_ins(words, user)

    def _split_sentences(self, text):
        ps = self._get_punctuation()
        ps = re.compile(u'[%s]' % ('|'.join(ps.keys())))
	det = ps.split(text)
	ret = filter(None, det)
        return ret

    def _get_chains(self, words):
        chain = []
        chains = []
        for word in words:
            chain.append(word)
            if len(chain) == self.num:
                values = [x['name'] for x in chain]
                chains.append(values)
                chain.pop(0)
        return chains

    def _get_chaindic(self, chains, user=''):
        isstart = True
        if user:
            if user not in self.userchaindic:
                self.userchaindic[user] = {}
            chaindic = self.userchaindic[user]
        else:
            chaindic = self.chaindic

        for chain in chains:
            prewords = tuple(chain[0:len(chain)-1])
            postword = chain[-1]
            if prewords not in chaindic:
                chaindic[prewords] = {}
            if postword not in chaindic[prewords]:
                chaindic[prewords][postword] = Chain(0, 0, isstart)
            chaindic[prewords][postword].count += 1
            if prewords[0] == u'。':
                isstart = True
            else:
                isstart = False

    def _update_newchains_ins(self, words, user=''):
        chainlist = self._get_chains(words)
        self._get_chaindic(chainlist, user) 

    def _get_words(self, text):
	words = text.split(' ')
        result = []
        isstart = False
        for i in xrange(len(words)):
            if i == len(words)-1:
                isstart = True
            else:
                isstart = False
            if i == 0:
                isstart = True
            result.append({'name': words[i], 'isstart': isstart})
        return result

    """
    連想配列を DB に保存
    """
    def register_data(self):
        self.register_chains()
        self.register_userchains()

    def register_chains(self):
        exists = self.db.get_allchain()

        for prewords in self.chaindic:
            for postword in self.chaindic[prewords]:
                count = self.chaindic[prewords][postword].count
                isstart = self.chaindic[prewords][postword].isstart
                chain = [prewords[0], prewords[1], postword, count, isstart]
                if tuple(chain[0:3]) in exists:
                    self.db.update_chain(chain)
                else:
                    self.db.insert_chain(chain)

    def register_userchains(self):
        exists = self.db.get_userchain()
        chains = self.userchaindic

        for user in chains:
            _user = self.db.update_user(user)
            for prewords in chains[user]:
                for postword in chains[user][prewords]:
                    count = chains[user][prewords][postword].count
                    isstart = chains[user][prewords][postword].isstart
                    chain = [prewords[0], prewords[1], postword, 
                             _user.key(), count, isstart]
                    if tuple(chain[0:4]) in exists:
                        self.db.update_userchain(chain)
                    else:
                        self.db.insert_userchain(chain)

    """
    文章生成
    """
    def make_sentence(self, user=None, word=None):
        limit = 1

        if user is None or user not in self.userchaindic:
            chaindic = self.chaindic
        else:
            chaindic = self.userchaindic[user]
        
        if word:
            prewords_tuple = chaindic.keys()
            for _prewords in prewords_tuple:
                if _prewords[0] == word:
                    break
            else:
                return ''

            while True:
                prewords = random.choice(chaindic.keys())
                if prewords[0] == word:
                    break
            postword = random.choice(chaindic[prewords].keys())
        else:
            while True:
                prewords = random.choice(chaindic.keys())
                postword = random.choice(chaindic[prewords].keys())
                if chaindic[prewords][postword].isstart:
                    break

        words = []
        words.extend(prewords)
        words.append(postword)

        while True:
            if postword in self._get_punctuation() and limit < len(words):
                return ' '.join(words)
            next_prewords = list(prewords[1:len(prewords)])
            next_prewords.append(postword)
            if tuple(next_prewords) not in chaindic:
                return ' '.join(words)

            postword = self._select_nextword_from_dic(chaindic, prewords)

            postword = random.choice(chaindic[tuple(next_prewords)].keys())
            prewords = next_prewords
            words.append(postword)

    def _select_nextword_from_dic(self, chaindic, _prewords):
        sum_count = 0
        prewords = tuple(_prewords)
        for postword in chaindic[prewords]:
            sum_count += chaindic[prewords][postword].count

        postwords = []

        for postword in chaindic[prewords]:
            info = Word(id=1, name=postword,
                count=chaindic[prewords][postword].count/float(sum_count))
            postwords.append(info)

        return Util.select_nextword(postwords)

    def show_chaindic(self):
	for a in self.chaindic:
        	print a 
		print self.chaindic[a]
		print " "

#training set must be in Unicode
if __name__ == '__main__':
	obj = MarkovChains(order_num=2)
	obj.analyze_sentence(u'I am a boy. You are a girl. It is a dog.')
	obj.analyze_sentence(u'She is a star. It is a bus. He is a cat.')
#	obj.show_chaindic()
	print obj.make_sentence()
