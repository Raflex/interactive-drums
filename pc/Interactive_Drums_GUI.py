from Tkinter import *
from threading import Thread
import glob
import tkFont
import re
import drumserial as ds
import midiparser as mp
import time

mode = "none"
currentSong = None
packets = []
paused = True
stop = True
thread = None

drums = ds.DrumSerial('/dev/ttyUSB0')

# finds all .mid files in the same directory as this file and displays
# them alphabetically
songs = glob.glob("*.mid")
songs.sort()
finalSongs = []
for i in songs:
    i = re.sub('.mid', ' ', i)
    finalSongs.append(i)


def menuClicked():
    songSelectionFrame.pack_forget()
    mainFrame.pack(fill=BOTH, expand=1)


def displaySongs():
    songSelectionFrame.pack(fill=BOTH, expand=1)


def scoreModeClicked():
    mainFrame.pack_forget()
    global mode
    mode = "score"
    displaySongs()


def trainingModeClicked():
    mainFrame.pack_forget()
    global mode
    mode = "training"
    displaySongs()


def freePlayModeClicked():
    mainFrame.pack_forget()
    global mode
    mode = "free"
    displaySongs()


def pausePlayClicked():
    global paused, thread, stop
    if stop:
        paused = False
        stop = False
        pausePlayButton['text'] = 'Pause'
        thread.start()
    else:
        paused = not paused
        pausePlayButton['text'] = 'Play' if paused else 'Pause'


def playSong():
    global packets, thread, currentSong
    songSelectionFrame.pack_forget()
    songPlayingFrame.pack(fill=BOTH, expand=1)
    songPlayingLabel['text'] = currentSong
    createSongThread()


def createSongThread():
    global packets, thread
    drums.flush_buffers()
    packets = mp.midi_to_packets(re.sub(' ', '.mid', currentSong))
    thread = Thread(target=songThread)


def songThread():
    global packets, drums
    packetsRemaining = len(packets)
    time.sleep(3)
    for i in range(12):
        drums.send(packets.pop(0))
        if handleStop():
            return

    waitOnPause()
    while packetsRemaining > 0:
        if (drums.check_for_packet()):
            print ds.parse_packet(drums.receive())
            packetsRemaining -= 1
            if (len(packets) > 0):
                drums.send(packets.pop(0))
        waitOnPause()
        if handleStop():
            return


def waitOnPause():
    global paused
    if paused is True:
        drums.send(ds.create_packet(0, 2, 0, 0))
        while paused:
            if handleStop():
                return
            pass
        drums.send(ds.create_packet(0, 3, 0, 0))


def handleStop():
    global stop, drums
    if stop is True:
        drums.send(ds.create_packet(0, 1, 0, 0))
    return stop


def on_select(event):
    playButton['state'] = 'active'
    selected = reduce(lambda rst, d: rst * 10 + d, event.widget.curselection())
    global currentSong
    currentSong = finalSongs[selected]


def backClicked():
    global stop
    songPlayingFrame.pack_forget()
    displaySongs()
    stop = True


def stopClicked():
    global stop, thread
    stop = True
    if isinstance(thread, Thread):
        if thread.isAlive():
            thread.join()
    createSongThread()


def onClose():
    global thread, stop
    stop = True
    if isinstance(thread, Thread):
        if thread.isAlive():
            thread.join()
    drums.close()
    mainWindow.quit()

mainWindow = Tk()
mainWindow.protocol("WM_DELETE_WINDOW", onClose)

# window title
mainWindow.title("Interactive Drums")

# window dimensions
mainWindow.minsize(800, 500)
mainWindow.geometry("1100x700")

largeFont = tkFont.Font(family="Helvetica", size=36)
smallFont = tkFont.Font(family="Helvetica", size=18)

###################### Start Main Menu frame and buttons  ######################
mainFrame = Frame(mainWindow)
mainFrame.pack(fill=BOTH, expand=1)

scoreFrame = Frame(mainFrame, bd=7)
scoreFrame.pack(side=TOP, fill=BOTH, expand=1)
scoreModeButton = Button(scoreFrame, text="Score Mode",
                         command=scoreModeClicked, font=largeFont)
scoreModeButton.pack(fill=BOTH, expand=1)

freePlayFrame = Frame(mainFrame, bd=7)
freePlayFrame.pack(side=BOTTOM, fill=BOTH, expand=1)
freePlayButton = Button(freePlayFrame, text="Free Play Mode",
                        command=freePlayModeClicked, font=largeFont)
freePlayButton.pack(fill=BOTH, expand=1)

trainingFrame = Frame(mainFrame, bd=7)
trainingFrame.pack(side=BOTTOM, fill=BOTH, expand=1)
trainingModeButton = Button(trainingFrame, text="Training Mode",
                            command=trainingModeClicked, font=largeFont)
trainingModeButton.pack(fill=BOTH, expand=1)
###################### End Main Menu frame and buttons  ########################


#################### Start Song Selection frame and buttons ####################
songSelectionFrame = Frame(mainWindow)

songList = StringVar()
songstring = "".join(finalSongs)
songList.set(songstring)


songSelectionListFrame = Frame(songSelectionFrame, padx=40, pady=20)
songSelectionListFrame.pack(anchor="n", side=BOTTOM, expand=1, fill=BOTH)
scrollbar = Scrollbar(songSelectionListFrame, orient=VERTICAL)
songSelectionList = Listbox(songSelectionListFrame,
                            listvariable=songList, font=smallFont)
scrollbar.config(command=songSelectionList.yview)
scrollbar.pack(side=RIGHT, fill=Y)
songSelectionList.pack(fill=BOTH, expand=1)
songSelectionList.bind("<ButtonRelease-1>", on_select)


menuButtonFrame = Frame(songSelectionFrame)
menuButtonFrame.pack(anchor='nw', side=LEFT, expand=1)
menuButton = Button(menuButtonFrame, text="Main Menu",
                    command=menuClicked, font=smallFont)
menuButton.pack()

songSelectionLabelFrame = Frame(songSelectionFrame)
songSelectionLabelFrame.pack(anchor='n', side=LEFT, expand=1)
songSelectionLabel = Label(songSelectionLabelFrame,
                           text="Select a Song to Play", font=largeFont)
songSelectionLabel.pack()

playButtonFrame = Frame(songSelectionFrame)
playButtonFrame.pack(anchor='ne', side=LEFT, expand=1)
playButton = Button(playButtonFrame, text="Play Song", font=smallFont,
                    state=DISABLED, command=playSong)
playButton.pack()
##################### End Song Selection frame and buttons #####################


###################### Start Song Playing fram and buttons #####################
songPlayingFrame = Frame(mainWindow)

songPlayingLabel = Label(songPlayingFrame, font=largeFont)
songPlayingLabel.pack()

backButtonFrame = Frame(songPlayingFrame)
backButtonFrame.pack(anchor='nw', side=LEFT, expand=1)
backButton = Button(backButtonFrame, text="Back",
                    command=backClicked, font=smallFont)
backButton.pack()

pausePlayButtonFrame = Frame(songPlayingFrame)
pausePlayButtonFrame.pack(anchor='ne', side=LEFT, expand=1)
pausePlayButton = Button(pausePlayButtonFrame, text="Play",
                         font=smallFont, command=pausePlayClicked)
pausePlayButton.pack()
###################### End Song Playing frame and buttons ######################

# start event loop
mainWindow.mainloop()
