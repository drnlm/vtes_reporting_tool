# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2013 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL v2 or later - see LICENSE & GPL.txt for details

"""A simple tool for helping track VTES games on android phones"""

import kivy

kivy.require('1.6.0')

#from kivy.logger import Logger, LoggerHistory
#for hdlr in Logger.handlers[:]:
#   if not isinstance(hdlr, LoggerHistory):
#       Logger.removeHandler(hdlr)


from kivy.app import App
from kivy.utils import escape_markup
from kivy.uix.widget import Widget
from kivy.uix.button import Button
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
        self._bOusted = False
        self.iPool = 30
        self.aMinions = []
        self.aMasters = []
        self.unhighlight_player()

    def add_minion(self):
        sMinion = 'Minion %d' % (len(self.aMinions) + 1)
        self.aMinions.append(sMinion)
        self._update_game()

    def add_master(self):
        sMaster = 'Master %d' % (len(self.aMasters) + 1)
        self.aMasters.append(sMaster)
        self._update_game()

    def change_pool(self, iChg):
        self.iPool += iChg
        self._update_game()

    def _update_game(self):
        for widget in self.game.children[:]:
            if not isinstance(widget, Button):
                self.game.remove_widget(widget)
        oPool = Label(text="[color=ff0022]%d[/color]" % self.iPool,
                      markup=True, pos_hint={'right': 1, 'top': 1},
                      size_hint=(None, None))
        self.game.add_widget(oPool)
        y = 0.9
        for sMinion in self.aMinions:
            oMinion = Label(text=sMinion,
                            pos_hint={'right': 0.3, 'top': y},
                            size_hint=(None, None))
            y -= 0.1
            self.game.add_widget(oMinion)

    def change(self, iDir):
        self.oParent.change(iDir)

    def next_turn(self):
        self.oParent.next_turn()

    def oust(self):
        self._bOusted = True
        self.oParent.oust()

    def set_details(self, sPlayer, sDeck):
        self._sPlayer = sPlayer
        self._sDeck = sDeck

    def update_decks(self):
        self.oParent.update_decks()

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
        label = self._get_round_label()
        self.player.add_widget(label)
        self._update_game()

    def get_turn_status(self):
        if self._bOusted:
            return '%s (ousted)' % self._sPlayer
        sMinions = '),  ('.join(self.aMinions)
        return '%s: %d pool, minions: (%s)' % (self._sPlayer,
                                               self.iPool, sMinions)

    def unhighlight_player(self):
        for label in self.player.children[:]:
            self.player.remove_widget(label)
        if not self._bOusted:
            sColor = 'aaaaaa'
            sOusted = ''
        else:
            sColor = 'ff3333'
            sOusted = ' (ousted)'
        if self._sDeck:
            label = Label(
                text="[b][color=%s]%s [i](playing %s)%s[/i]"
                "[/color][/b]" % (sColor, escape_markup(self._sPlayer),
                                  escape_markup(self._sDeck), sOusted),
                font_size=15, markup=True)
        else:
            label = Label(
                text="[b][color=%s]%s [i](unspecfied)%s"
                "[/i][/color][/b] " % (sColor, escape_markup(self._sPlayer),
                                       sOusted),
                font_size=15, markup=True)
        self.player.add_widget(label)
        label = self._get_round_label()
        self.player.add_widget(label)
        self._update_game()

    def _get_round_label(self):
        label = Label(text="[color=33ff33]Round %d.%d (%d players)[/color]"
                      % self.oParent.get_round(), markup=True)
        return label


class GameReportWidget(Carousel):

    def __init__(self, oParent):
        super(GameReportWidget, self).__init__()
        self.oParent = oParent
        self.iCur = 0
        self.iScreen = 0
        self.aPlayers = []
        self.dDecks = {}
        self.dLog = {}
        self.iRound = 1
        self.aOusted = set()
        self.loop = True

    def set_players(self, aPlayers):
        self.aPlayers = aPlayers

    def set_decks(self, dDecks):
        self.dDecks = dDecks

    def update_details(self):
        for oScreen, sPlayer in zip(self.slides, self.aPlayers):
            if sPlayer in self.dDecks:
                sDeck = self.dDecks[sPlayer]
            else:
                sDeck = ''
            oScreen.set_details(sPlayer, sDeck)
        for oScreen in self.slides:
            oScreen.unhighlight_player()
        self.slides[self.iCur].highlight_player()

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

    def step_current(self):
        self.iCur += 1
        if self.iCur >= len(self.aPlayers):
            self.iCur = 0
            self.iRound += 1

    def get_round(self):
        return self.iRound, self.iCur + 1, len(self.aPlayers)

    def get_round_key(self):
        return '%d.%d' % (self.iRound, self.iCur + 1)

    def next_turn(self):
        self.step_current()
        if len(self.aOusted) == len(self.aPlayers):
            self.iCur = 0
        else:
            while self.iCur in self.aOusted:
                self.step_current()
        aTurn = []
        for oScreen in self.slides:
            oScreen.unhighlight_player()
            aTurn.append(oScreen.get_turn_status())
        if self.iCur not in self.aOusted:
            self.slides[self.iCur].highlight_player()
        # We set things up so we can animate a scroll to the current player
        self.dLog[self.get_round_key()] = '\n'.join(aTurn)
        if self.index != self.iCur:
            if self.iCur > 0:
                self.index = self.iCur - 1
            else:
                self.index = len(self.aPlayers) - 1
            self.load_next()

    def oust(self):
        self.aOusted.add(self.index)
        self.slides[self.index].unhighlight_player()
        if self.index == self.iCur:
            self.next_turn()

    def update_decks(self):
        self.oParent.update_decks()

    def stop_game(self):
        self.oParent.stop_game()
        print self.dLog


class PlayerSelectWidget(Widget):

    input_area = ObjectProperty(None)
    start_button = ObjectProperty(None)

    def __init__(self, oParent):
        super(PlayerSelectWidget, self).__init__()
        self._sMode = 'Start'
        self.oParent = oParent
        self._aNameWidgets = []
        self._aDeckWidgets = []
        for i in range(1, 8):
            bot = 1 - 0.125 * i
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

    def set_start_mode(self):
        self._sMode = 'Start'
        self.start_button.text = self._sMode

    def set_resume_mode(self):
        self._sMode = 'Resume'
        self.start_button.text = self._sMode

    def start(self):
        aPlayers = []
        dDecks = {}
        for oPlayer, oDeck in zip(self._aNameWidgets, self._aDeckWidgets):
            if oPlayer.text.strip():
                aPlayers.append(oPlayer.text.strip())
                if oDeck.text.strip():
                    dDecks[oPlayer.text.strip()] = oDeck.text.strip()

        if self._sMode == 'Start':
            self.parent.start_game(aPlayers, dDecks)
        else:
            self.parent.resume_game(aPlayers, dDecks)


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
        self.select.set_start_mode()
        self.add_widget(self.select)

    def update_decks(self):
        self.remove_widget(self.game)
        self.select.set_resume_mode()
        self.add_widget(self.select)

    def resume_game(self, aPlayers, dDecks):
        self.game.set_players(aPlayers)
        self.game.set_decks(dDecks)
        self.game.update_details()
        self.remove_widget(self.select)
        self.add_widget(self.game)


class VTESGameApp(App):

    title = "VTES Game Reporter"

    def build(self):
        return GameWidget()

if __name__ == "__main__":
    VTESGameApp().run()
