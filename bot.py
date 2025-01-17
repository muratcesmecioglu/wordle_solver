import random
import numpy as np
import pandas as pd
import builtins
from forbiddenfruit import curse

lcase_table = tuple(u'abcçdefgğhıijklmnoöprsştuüvyz')
ucase_table = tuple(u'ABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ')

def upper(data):
    data = data.replace('i',u'İ')
    data = data.replace(u'ı',u'I')
    result = ''
    for char in data:
        try:
            char_index = lcase_table.index(char)
            ucase_char = ucase_table[char_index]
        except:
            ucase_char = char
        result += ucase_char
    return result

def lower(data):
    data = data.replace(u'İ',u'i')
    data = data.replace(u'I',u'ı')
    result = ''
    for char in data:
        try:
            char_index = ucase_table.index(char)
            lcase_char = lcase_table[char_index]
        except:
            lcase_char = char
        result += lcase_char
    return result

def capitalize(data):
    return data[0].upper() + data[1:].lower()

def title(data):
    return " ".join(map(lambda x: x.capitalize(), data.split()))

curse(str, 'upper', upper)
curse(str, 'lower', lower)
curse(str, 'capitalize', capitalize)
curse(str, 'title', title)

class Agent:
    def __init__(self, game, f_name='data/words.csv'):
        self.vowels = ['A','E','I','İ','O','Ö','U','Ü']
        w_bank = pd.read_csv(f_name)
        w_bank = w_bank[w_bank['words'].str.len()==game.letters]
        w_bank['words'] = w_bank['words'].str.upper() #Convert all words to uppercase
        w_bank['v-count'] = w_bank['words'].apply(lambda x: ''.join(set(x))).str.count('|'.join(self.vowels)) #Count amount of vowels in words
        self.w_bank = w_bank
        self.game = game
        self.prediction = ['' for _ in range(game.letters)]
        self.y_letters = {}
        self.g_letters = []

    def calc_letter_probs(self):
        for x in range(self.game.letters):
            counts = self.w_bank['words'].str[x].value_counts(normalize=True).to_dict()
            self.w_bank[f'p-{x}'] = self.w_bank['words'].str[x].map(counts)

    def parse_board(self):
        if self.game.g_count > 0:
            for x, c in enumerate(self.game.colours[self.game.g_count - 1]):
                letter = self.game.board[self.game.g_count - 1][x]
                if c == 'Y':
                    if letter not in self.y_letters:
                        self.y_letters[letter] = [x]
                    else:
                        if x not in self.y_letters[letter]:
                            self.y_letters[letter].append(x)
                elif c == 'G':
                    self.prediction[x] = letter
                else:
                    if letter in ''.join(self.prediction):
                        if letter not in self.y_letters:
                            self.y_letters[letter] = [x]
                        else:
                            self.y_letters[letter].append(x)
                    elif letter not in self.g_letters:
                        self.g_letters.append(letter)
            self.g_letters = [l for l in self.g_letters if l not in self.y_letters]

    def choose_action(self):
        self.parse_board()
        if len(self.g_letters) > 0:
            self.w_bank = self.w_bank[~self.w_bank['words'].str.contains('|'.join(self.g_letters))]
            self.g_letters = []
        if len(self.y_letters) > 0:
            y_str = '^' + ''.join(fr'(?=.*{l})' for l in self.y_letters)
            self.w_bank = self.w_bank[self.w_bank['words'].str.contains(y_str)]
            for s, p in self.y_letters.items():
                for i in p:
                    self.w_bank = self.w_bank[self.w_bank['words'].str[i]!=s]
            self.y_letters = {}
        for i, s in enumerate(self.prediction):
            if s != '':
                self.w_bank = self.w_bank[self.w_bank['words'].str[i]==s]
        self.w_bank['w-score'] = [0] * len(self.w_bank)
        if len(self.w_bank) > 5:
            self.calc_letter_probs() #Recalculate letter position probability
        for x in range(self.game.letters):
            if self.prediction[x] == '':
                self.w_bank['w-score'] += self.w_bank[f'p-{x}']
        if True not in [True for s in self.prediction if s in self.vowels]:
            self.w_bank['w-score'] += self.w_bank['v-count'] / self.game.letters
        mv_bank = self.w_bank[self.w_bank['w-score']==self.w_bank['w-score'].max()]
        result = random.choice(mv_bank['words'].tolist())
        return result
