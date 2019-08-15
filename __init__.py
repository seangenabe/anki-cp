from aqt import mw
from aqt.utils import showInfo, chooseList, showText
from aqt.qt import *
from itertools import chain
from anki.utils import stripHTMLMedia, intTime, ids2str
import time

def copyScheduling(deckFrom, deckTo):
  now = intTime()
  logs = []
  cids = mw.col.decks.cids(deckTo["id"], children=False)
  copiedN = 0
  updates = []
  revlogid = int(time.time() * 1000)
  
  for cid in cids:
    card = mw.col.getCard(cid)
    note = mw.col.getNote(card.nid)
    sfld = stripHTMLMedia(note.fields[note.col.models.sortIdx(note._model)])
    sourceCids = mw.col.db.list(
      "select distinct(c.id) from cards c, notes n where c.nid=n.id and c.did=? and n.sfld=?",
      deckFrom["id"],
      sfld
    )
    
    # If there are no source cards, skip
    if not sourceCids:
      continue
    if len(sourceCids) > 1:
      logs.append("Multiple source cards not supported. Matched field={0}".format(sfld))
      continue
    sourceCid = sourceCids[0]
    sourceCard = mw.col.getCard(sourceCid)
    # Skip new cards
    if sourceCard.queue == 0:
      continue

    logs.append("Matched card {0}".format(sfld))
    
    updates.append(dict(
      cid=cid,
      due=sourceCard.due,
      queue=sourceCard.queue,
      ivl=sourceCard.ivl,
      factor=sourceCard.factor,
      left=sourceCard.left,
      type=sourceCard.type,
      now=now,
      usn=mw.col.usn()
    ))

    def copyRevlog():
      mw.col.db.execute(
        "insert into revlog "
        "select :id, :newcid, :usn, r.ease, r.ivl, r.lastIvl, r.factor, r.time, r.type "
        "from revlog as r "
        "where cid=:oldcid",
        id=revlogid,
        oldcid=sourceCid,
        newcid=cid,
        usn=mw.col.usn()
      )
    for _ in range(0, 5):
      try:
        copyRevlog()
        break
      finally:
        revlogid += 1
    copyRevlog()
    
    copiedN += 1

  #logs.append("updates {0}".format(updates))

  mw.col.db.executemany(
    "update cards set "
    "due=:due, mod=:now, usn=:usn, queue=:queue, "
    "ivl=:ivl, factor=:factor, left=:left, type=:type "
    "where id=:cid",
    updates
  )
  
  logs.append("Copied {0} cards".format(copiedN))

  showText("\n".join(logs), title="Copy scheduling log")
  mw.reset()

def copyScheduling():
  decks = mw.col.decks.all()

  deckFromIndex = chooseList("Choose deck to copy from", chain(map(lambda deck: deck['name'], decks), ["Cancel"]))
  if deckFromIndex == len(decks):
    return
  otherDecks = decks.copy()
  otherDecks.pop(deckFromIndex)
  deckToIndex = chooseList("Choose deck to copy to", chain(map(lambda deck: deck['name'], otherDecks), ["Cancel"]))
  if deckToIndex == len(otherDecks):
    return
  
  deckFrom = decks[deckFromIndex]
  deckTo = otherDecks[deckToIndex]

  mw.checkpoint("Copy scheduling")
  try:
    copyScheduling(deckFrom, deckTo)
  except:
    mw.col.db.rollback()
    raise

action = QAction("Copy Scheduling", mw)
action.triggered.connect(copyScheduling)

mw.form.menuTools.addAction(action)
