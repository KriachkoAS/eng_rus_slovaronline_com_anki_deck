from aqt import mw
from aqt.qt import QAction
from aqt.utils import qconnect, showInfo
import sqlite3
import re
from collections import defaultdict
import array



def escape_characters(val: str) -> str:
    return '"' + val.replace('"', '\\"') + '"' if ' ' in val else val

def estmate_defs_count(meaning: str, pattern = re.compile(r'II+|[0-9][0-9]+[.\)]|[02-9][.\)]')) -> str:
    return 1 + len(list(re.finditer(pattern, meaning)))

def sort_key(ffreq: float, known_probability: float, defs_count: int) -> float:
    return -ffreq*(1-known_probability)/defs_count


def set_sort_field() -> None:
    config = mw.addonManager.getConfig(__name__)
    KNOWN_WRITTEN_WORD_AMOUNT = 23234
    with sqlite3.connect(__file__[:-11] + 'ffreq.db') as con:
        preitems = [(row[0], [row[1]]) for row in con.execute('select * from ffreq')]
    words_vals = sorted([preitem[0] for preitem in preitems if preitem[1][0] != 0])
    py_arr = array.array('d')
    with open(__file__[:-11] + 'known_probability_raw', 'br') as f: 
        py_arr.fromfile(f, KNOWN_WRITTEN_WORD_AMOUNT*160)
    probs = defaultdict(lambda : 0)
    if config['known_words_count'] >= 100:
        for word, prob in zip(words_vals, py_arr[KNOWN_WRITTEN_WORD_AMOUNT*(config['known_words_count']//100-1):KNOWN_WRITTEN_WORD_AMOUNT*config['known_words_count']//100]):
            probs[word] = prob
    for preitem in preitems:
        preitem[1].append(probs[preitem[0]])
    del words_vals, py_arr, probs
    items = []
    for preitem in preitems:
        found_cards = mw.col.find_cards('deck:{} {}:{}'.format(escape_characters(config['deck']), escape_characters(config['word_field']), escape_characters(preitem[0])))
        if len(found_cards) == 1:
            items.append([preitem[0], preitem[1] + [estmate_defs_count(mw.col.get_note(mw.col.get_card(found_cards[0]).nid)[config['meaning_field']])]])
    items.sort(key=lambda item: sort_key(*item[1]))
    item_counter = 0
    for item in items:
        found_notes = mw.col.find_notes('deck:{} {}:{}'.format(escape_characters(config['deck']), escape_characters(config['word_field']), item[0]))
        note = mw.col.get_note(found_notes[0])
        note[config['sort_field']] = "{:6}".format(item_counter)
        mw.col.update_note(note)
        item_counter += 1



action = QAction("sort slovaronline", mw)
qconnect(action.triggered, set_sort_field)
mw.form.menuTools.addAction(action)