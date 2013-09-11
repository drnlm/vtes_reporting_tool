import kivy

kivy.require('1.6.0')

from kivy.logger import Logger, LoggerHistory
#for hdlr in Logger.handlers[:]:
#   if not isinstance(hdlr, LoggerHistory):
#       Logger.removeHandler(hdlr)


from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.carousel import Carousel


class PlayerScreen(RelativeLayout):

    game = ObjectProperty(None)
    player = ObjectProperty(None)

    def __init__(self, oParent, sPlayer, sDeck):
        super(PlayerScreen, self).__init__()
        self.oParent = oParent
        if sDeck:
            label = Label(text="%s (playing %s)" % (sPlayer, sDeck))
        else:
            label = Label(text="%s (unspecfied)" % sPlayer)
        self.player.add_widget(label)

    def change(self, iDir):
        self.oParent.change(iDir)
        
    def next_turn(self):
        self.oParent.next_turn()

    def oust(self):
        self.oParent.oust()

    def stop_game(self):
        self.oParent.stop_game()


class GameReportWidget(Carousel):

    def __init__(self, oParent):
        super(GameReportWidget, self).__init__()
        self.oParent = oParent
        self.iCur = 0
        self.iScreen = 0
        self.aPlayers = []
        self.dDecks = {}
        self.aLog = []
        self.aScreens = []
        self.loop = True

    def set_players(self, aPlayers):
        self.aPlayers = aPlayers

    def set_decks(self, dDecks):
        self.dDecks = dDecks

    def add_screens(self):
        for oWidget in self.children[:]:
            self.remove_widget(oWidget)
        self.aScreens = []
        for sPlayer in self.aPlayers:
            if sPlayer in self.dDecks:
                sDeck = self.dDecks[sPlayer]
            else:
                sDeck = ''
            oScreen = PlayerScreen(self, sPlayer, sDeck)
            self.aScreens.append(sPlayer)
            self.add_widget(oScreen)

    def change(self, iDir):
        self.iScreen += iDir
        if self.iScreen < 0:
            self.iScreen = len(self.aScreens) - 1
        elif self.iScreen >= len(self.aScreens):
            self.iScreen = 0
        if iDir < 0:
            self.load_previous()
        else:
            self.load_next()

    def next_turn(self):
        self.iCur += 1
        if self.iCur >= len(self.aPlayers):
            self.iCur = 0
        self.change(+1)

    def oust(self):
        pass

    def stop_game(self):
        self.oParent.stop_game()



class PlayerSelectWidget(Widget):

    grid = ObjectProperty(None)

    def __init__(self, oParent):
        super(PlayerSelectWidget, self).__init__()
        self.oParent = oParent
        self._aNameWidgets = []
        self._aDeckWidgets = []
        for i in range(1, 8):
            self.grid.add_widget(Label(text="Player %d : " % i))
            oTextInput = TextInput(multiline=False)
            self.grid.add_widget(oTextInput)
            self._aNameWidgets.append(oTextInput)
            self.grid.add_widget(Label(text=" playing Deck : "))
            oTextInput = TextInput(multiline=False)
            self.grid.add_widget(oTextInput)
            self._aDeckWidgets.append(oTextInput)

    def start(self):
        aPlayers = []
        dDecks = {}
        for oPlayer, oDeck in zip(self._aNameWidgets, self._aDeckWidgets):
            if oPlayer.text.strip():
                aPlayers.append(oPlayer.text.strip())
                if oDeck.text.strip():
                    dDecks[oPlayer.text.strip()] = oDeck.text.strip()
        self.parent.start_game(aPlayers, dDecks)


class GameWidget(BoxLayout):

    def __init__(self):
        super(GameWidget, self).__init__()
        self.select = PlayerSelectWidget(self)
        self.game = None
        self.add_widget(self.select)

    def start_game(self, aPlayers, dDecks):
        self.game = GameReportWidget(self)
        self.remove_widget(self.select)
        self.game.set_players(aPlayers)
        self.game.set_decks(dDecks)
        self.game.add_screens()
        self.add_widget(self.game)

    def stop_game(self):
        self.remove_widget(self.game)
        self.game = None
        self.add_widget(self.select)


class VTESGameApp(App):

   title = "VTES Game Reporter"

   def build(self):
       return GameWidget()

if __name__ == "__main__":
   VTESGameApp().run()
