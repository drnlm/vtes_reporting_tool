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


class GameReportWidget(Widget):

    game = ObjectProperty(None)
    players = ObjectProperty(None)

    def __init__(self, oParent):
        super(GameReportWidget, self).__init__()
        self.oParent = oParent
        self.iCur = 0
        self.aPlayer = []
        self.dDecks = {}
        self.aLog = []

    def set_players(self, aPlayers):
        self.aPlayers = aPlayers

    def set_decks(self, dDecks):
        self.dDecks = dDecks
        y_size = 120 // len(self.aPlayers)
        for oWidget in self.players.children[:]:
            self.players.remove_widget(oWidget)
        for sPlayer in self.aPlayers:
            if sPlayer in self.dDecks:
                label = Label(text='%s (%s) bleeding' % (
                    sPlayer, self.dDecks[sPlayer]), size_hint_y=y_size)
            else:
                label = Label(text='%s bleeding' % sPlayer,
                              size_hint_y=y_size)
            self.players.add_widget(label)

    def next(self):
        self.iCur += 1
        if self.iCur >= len(self.aPlayers):
            self.iCur = 0

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
        self.game = GameReportWidget(self)
        self.add_widget(self.select)

    def start_game(self, aPlayers, dDecks):
        self.remove_widget(self.select)
        self.game.set_players(aPlayers)
        self.game.set_decks(dDecks)
        self.add_widget(self.game)

    def stop_game(self):
        self.remove_widget(self.game)
        self.add_widget(self.select)


class VTESGameApp(App):

   title = "VTES Game Reporter"

   def build(self):
       return GameWidget()

if __name__ == "__main__":
   VTESGameApp().run()
