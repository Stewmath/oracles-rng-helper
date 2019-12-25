#!/usr/bin/python3
import curses

class RNGState:
    def __init__(self):
        self.rng1 = 0x37
        self.rng2 = 0x0d

    def advance(self):
        word = self.rng1 | (self.rng2 << 8)
        word = word * 3
        self.rng2 = (word >> 8) & 0xff
        self.rng1 = (self.rng2 + self.rng1) & 0xff
        return self.rng1

    def get(self):
        return self.rng1

    def copy(self):
        ret = RNGState()
        ret.rng1 = self.rng1
        ret.rng2 = self.rng2
        return ret

    def __eq__(self, other):
        return self.rng1 == other.rng1 and self.rng2 == other.rng2

    def __hash__(self):
        return self.rng1 + (self.rng2<<8)


# Generate the full RNG sequence. (It loops.)
rngSequence = []
rngSet = set()

rng = RNGState()
rngSet.add(rng)
while True:
    rngSequence.append(rng.copy())
    rng.advance()

    if rng in rngSet:
        # Looped
        assert(rng.rng1 == 0x37)
        assert(rng.rng2 == 0x0d)
        break
    rngSet.add(rng)


# Search for a particular sequence. The parameter "sequence" is actually a list
# of functions to match against the RNG state.
def findSequence(sequence):
    rng = RNGState()
    pos = 0
    while True:
        ok = True
        rngCopy = rng.copy()
        for j in range(len(sequence)):
            if not sequence[j](rngCopy):
                ok = False
                break
        if ok:
            yield pos

        rng.advance()
        pos+=1
        if pos >= len(rngSequence):
            break


# Functions to pass to "findSequence" corresponding to certain actions

# "slashSeq" returns a function which matches a set of slash sounds.
slashTable = 'MHLMMHMM'
slashDict = dict( (s,[i for (i,v) in enumerate(slashTable) if v == s]) for s in ['L','M','H'])
def slashSeq(slashes):
    def slashSeqHelper(rng):
        for slash in slashes:
            if not (rng.advance() & 7) in slashDict[slash]:
                return False
        return True

    return slashSeqHelper



# Helper functions

def myhex(val, length=1):
    if val < 0:
        return "-" + myhex(-val, length)
    out = hex(val)[2:]
    while len(out) < length:
        out = '0' + out
    return out


# Ncurses stuff

def refreshScreen(sequence):
    stdscr.clear()
    stdscr.addstr(0, 0, 'Enter the sequence of sword swings.')
    stdscr.addstr(2, 0, 'Sequence: ' + ''.join(sequence))
    matches = list(findSequence([slashSeq(sequence)]))
    stdscr.addstr(4, 0, 'Matches: ' + str(len(matches)))

    row = 6

    if len(matches) == 0:
        stdscr.addstr(6, 0, 'No match, did you make a mistake inputting the sounds?')
    elif 0: # Just show the match
        if len(matches) <= 5:
            for matchIndex,match in enumerate(matches):
                stdscr.addstr(row, 0, 'MATCH ' + str(matchIndex+1))
                rng = rngSequence[match]
                stdscr.addstr(row+1, 4, 'RNG1: 0x' + myhex(rng.rng1, 2) + '; RNG2: 0x' + myhex(rng.rng2, 2))

                row += 3

    elif 1: # D6 levers; show # of advances until you can pull
        ok = True
        if len(matches) <= 20:
            lastCount = -1
            for match in matches:
                rng = rngSequence[match].copy()
                for i in range(len(sequence)+1):
                    rng.advance()
                count=0
                while True:
                    if rng.get()%4 == 0:
                        break
                    rng.advance()
                    count+=1
                if lastCount != -1 and lastCount != count:
                    lastCount = -1
                    ok = False
                    break
                lastCount = count
        else:
            ok = False

        if ok:
            stdscr.addstr(row, 0, 'Slash ' + str(lastCount) + ' more times')
        else:
            stdscr.addstr(row, 0, 'No result yet, keep swinging the sword')


# Reads chars that correspond to slashes, and returns the capitalized "L/M/H".
def convertSlashChar(c):
    dict = {'L': ['L','l','1'],
            'M': ['M','m','2'],
            'H': ['H','h','3']}
    for d in 'LMH':
        if c in dict[d]:
            return d

if __name__ == "__main__":
    try:
        stdscr = curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.curs_set(False)
        stdscr.keypad(True)

        sequence = []
        refreshScreen(sequence)

        while True:
            c = stdscr.getch()
            if c == 127: # Backspace
                if len(sequence) != 0:
                    sequence.pop()
            elif c == ord('r') or c == ord('R'):
                sequence = []
            elif convertSlashChar(chr(c)) is not None:
                sequence.append(convertSlashChar(chr(c)))
            refreshScreen(sequence)

    finally:
        curses.echo()
        curses.nocbreak()
        stdscr.keypad(False)
        curses.endwin()
