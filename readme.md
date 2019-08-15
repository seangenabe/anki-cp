# Anki Copy Scheduling add-on

This add-on copies scheduling info from one deck to another.

Use case: Migrating from a deck to another similar deck.

* Cards are compared by their sort field. Only cards with a matching sort field are processed.
  * Cards from the old deck that are "new" are ignored.
  * Cards that don't match a card in the old deck are ignored.
  * The scenario where there are multiple cards representing a note _in the old deck_ is not yet supported.
* All scheduling info are overwritten.
* All `revlog`s of the cards from the old deck are copied.
  * Make sure to run the process only once; the revlogs are copied each run.
* Undo support
