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


class GameWidget(Widget):

    grid = ObjectProperty()

    def __init__(self, **kwargs):
        super(GameWidget, self).__init__(**kwargs)
        self.aPlayers = []
        self.dDecks = {}
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
        for oPlayer, oDeck in zip(self._aNameWidgets, self._aDeckWidgets):
            if oPlayer.text.strip():
                self.aPlayers.append(oPlayer.text.strip())
                if oDeck.text.strip():
                    self.dDecks[oPlayer.text.strip()] = oDeck.text.strip()
        print self.aPlayers, self.dDecks




class VTESGameApp(App):

   title = "VTES Game Reporter"

   def __init__(self):
       super(VTESGameApp, self).__init__()

   def build(self):
       return GameWidget()

if __name__ == "__main__":
   VTESGameApp().run()
