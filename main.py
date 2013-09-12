import kivy

kivy.require('1.6.0')

#from kivy.logger import Logger, LoggerHistory
#for hdlr in Logger.handlers[:]:
#   if not isinstance(hdlr, LoggerHistory):
#       Logger.removeHandler(hdlr)


from kivy.app import App
from kivy.utils import escape_markup
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
        self._sPlayer = sPlayer
        self._sDeck = sDeck
        self._bHighlight = False
        self.unhighlight_player()

    def update_deck(self, sDeck):
        self._sDeck = sDeck
        if self._bHighlight:
            self.highlight_player()
        else:
            self.unhighlight_player()

    def change(self, iDir):
        self.oParent.change(iDir)

    def next_turn(self):
        self.oParent.next_turn()

    def oust(self):
        self.oParent.oust()

    def stop_game(self):
        self.oParent.stop_game()

    def highlight_player(self):
        for label in self.player.children[:]:
            self.player.remove_widget(label)
        if self._sDeck:
            label = Label(text="[b][color=00ffff]%s [i](playing %s)[/i]"
                          "[/color][/b]" % (escape_markup(self._sPlayer),
                                            escape_markup(self._sDeck)),
                          font_size=20, markup=True)
        else:
            label = Label(text="[b][color=00ffff]%s [i](unspecfied)"
                               "[/i][/color][/b] " % escape_markup(
                                   self._sPlayer),
                               font_size=20, markup=True)
        self.player.add_widget(label)

    def unhighlight_player(self):
        for label in self.player.children[:]:
            self.player.remove_widget(label)
        if self._sDeck:
            label = Label(
                text="[b][color=aaaaaa]%s [i](playing %s)[/i]"
                "[/color][/b]" % (escape_markup(self._sPlayer),
                                  escape_markup(self._sDeck)),
                font_size=15, markup=True)
        else:
            label = Label(
                text="[b][color=aaaaaa]%s [i](unspecfied)"
                "[/i][/color][/b] " % escape_markup(self._sPlayer),
                font_size=15, markup=True)
        self.player.add_widget(label)


class GameReportWidget(Carousel):

    def __init__(self, oParent):
        super(GameReportWidget, self).__init__()
        self.oParent = oParent
        self.iCur = 0
        self.iScreen = 0
        self.aPlayers = []
        self.dDecks = {}
        self.aLog = []
        self.loop = True

    def set_players(self, aPlayers):
        self.aPlayers = aPlayers

    def set_decks(self, dDecks):
        self.dDecks = dDecks

    def add_screens(self):
        for oWidget in self.children[:]:
            self.remove_widget(oWidget)
        for sPlayer in self.aPlayers:
            if sPlayer in self.dDecks:
                sDeck = self.dDecks[sPlayer]
            else:
                sDeck = ''
            oScreen = PlayerScreen(self, sPlayer, sDeck)
            self.add_widget(oScreen)
        self.slides[self.iCur].highlight_player()

    def change(self, iDir):
        self.iScreen += iDir
        if iDir < 0:
            self.load_previous()
        else:
            self.load_next()

    def next_turn(self):
        self.iCur += 1
        if self.iCur >= len(self.aPlayers):
            self.iCur = 0
        for oScreen in self.slides:
            oScreen.unhighlight_player()
        self.slides[self.iCur].highlight_player()
        # We set things up so we can animate a scroll to the current player
        if self.index != self.iCur:
            if self.iCur > 0:
                self.index = self.iCur - 1
            else:
                self.index = len(self.aPlayers) - 1
            self.load_next()

    def oust(self):
        pass

    def stop_game(self):
        self.oParent.stop_game()


class PlayerSelectWidget(Widget):

    input_area = ObjectProperty(None)

    def __init__(self, oParent):
        super(PlayerSelectWidget, self).__init__()
        self.oParent = oParent
        self._aNameWidgets = []
        self._aDeckWidgets = []
        for i in range(1, 8):
            bot = 1 - 0.125 * i
            print bot
            self.input_area.add_widget(Label(text="Player %d : " % i,
                                             size_hint=(0.2, 0.1),
                                             pos_hint={'right': 0.2,
                                                       'center_y': bot}))
            oTextInput = TextInput(multiline=False,
                                   size_hint=(0.3, 0.075),
                                   pos_hint={'right': 0.5, 'center_y': bot})
            self.input_area.add_widget(oTextInput)
            self._aNameWidgets.append(oTextInput)
            self.input_area.add_widget(Label(text=" playing Deck : ",
                                             size_hint=(0.2, 0.1),
                                             pos_hint={'right': 0.7,
                                                       'center_y': bot}))
            oTextInput = TextInput(multiline=False,
                                   size_hint=(0.3, 0.075),
                                   pos_hint={'right': 1, 'center_y': bot})
            self.input_area.add_widget(oTextInput)
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
