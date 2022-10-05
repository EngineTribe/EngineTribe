import sys
sys.path.append('../..')

from dfa_filter import DFAFilter
import requests
from config import OFFENSIVE_WORDS_LIST, OFFENSIVE_WORDS_LIST_CN_ONLY
import re

dfa_filter = DFAFilter()
for url in OFFENSIVE_WORDS_LIST:
    wordlist = requests.get(url=url).text.replace('\r', '').split('\n')
    for word in wordlist:
        if len(word) > 1:
            dfa_filter.add(word)
for url in OFFENSIVE_WORDS_LIST_CN_ONLY:
    wordlist = requests.get(url=url).text.replace('\r', '').split('\n')
    for word in wordlist:
        if len(re.findall(re.compile(r'[A-Za-z]', re.S), word)) == 0:
            if len(word) > 1:
                dfa_filter.add(word)

while True:
    sentence = input('Sentence: ')
    filtered = dfa_filter.filter(sentence)
    print(sentence)
    print(filtered)
