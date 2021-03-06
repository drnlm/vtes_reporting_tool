# -*- coding: utf-8 -*-
# vim:fileencoding=utf-8 ai ts=4 sts=4 et sw=4
# Copyright 2013 Neil Muller <drnlmuller+sutekh@gmail.com>
# GPL v2 or later - see LICENSE & GPL.txt for details

"""A simple tool for helping track VTES games on android phones"""


__version__ = '0.0.1'

import os
import datetime
import kivy

kivy.require('1.7.0')

#from kivy.logger import Logger, LoggerHistory
#for hdlr in Logger.handlers[:]:
#   if not isinstance(hdlr, LoggerHistory):
#       Logger.removeHandler(hdlr)


from kivy.app import App
from kivy.clock import Clock
from kivy.utils import escape_markup
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.properties import ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.carousel import Carousel
from kivy.adapters.listadapter import ListAdapter
from kivy.uix.listview import ListItemButton


class LoadDialog(Popup):

    def __init__(self, oParent):
        super(LoadDialog, self).__init__()
        self._oParent = oParent

    def load(self, filename):
        if filename:
            self._oParent.load(filename[0])
            self.dismiss()


class RollbackDialog(Popup):

    def __init__(self, oMainWidget, aRounds):
        self.turnadapt = ListAdapter(data=aRounds,
                                     args_converter=self.convert,
                                     cls=ListItemButton,
                                     selection_mode='single',
                                     allow_empty_selection=False)
        self.turnadapt.bind(selection=self.selection)
        self.oMainWidget = oMainWidget
        self.sRound = aRounds[0]
        super(RollbackDialog, self).__init__()

    def convert(self, iRow, sText):
        return {'text': sText,
                'size_hint_y': None, 'height': 25}

    def selection(self, oAdapt, *args):
        if self.turnadapt.selection:
            # We need this guard, since we're called twice on selection
            # changes - once with nothing selected and once with the
            # new selection
            self.sRound = self.turnadapt.selection[0].text

    def select(self):
        self.oMainWidget.rollback_to_round(self.sRound)
        self.dismiss()


class ActionResult(Popup):

    def __init__(self, oParent):
        super(ActionResult, self).__init__()
        self._oParent = oParent

    def resolved(self, sType):
        self._oParent.add_resolution(sType)
        self.dismiss()


class ActionChoice(Popup):

    def __init__(self, oParent):
        super(ActionChoice, self).__init__()
        self._oParent = oParent
        self._sAction = None

    def action(self, sType):
        self._sAction = sType
        oPopup = ActionResult(self)
        oPopup.open()

    def add_resolution(self, sResult):
        self._oParent.add_action(self._sAction, sResult)
        self.dismiss()


class EditBoxRow(BoxLayout):

    action = ObjectProperty(None)

    def __init__(self, oParent, iIndex, sAction):
        super(EditBoxRow, self).__init__()
        self._oParent = oParent
        self.action.text = sAction
        self._iIndex = iIndex

    def delete(self):
        self._oParent.remove_action(self._iIndex)

    def update_index(self, iIndex):
        if self._iIndex > iIndex:
            self._iIndex -= 1


class EditMinion(Popup):

    name = ObjectProperty(None)
    layout = ObjectProperty(None)

    def __init__(self, oParent, aActions):
        super(EditMinion, self).__init__()
        self._oParent = oParent
        self.name.text = oParent.get_name()
        self._aActions = aActions
        self._aActionWidgets = []
        for iIndex, sAction in enumerate(aActions):
            oWidget = EditBoxRow(self, iIndex, sAction)
            self._aActionWidgets.append(oWidget)
            self.layout.add_widget(oWidget)

    def rename(self):
        sNewName = self.name.text.strip()
        if sNewName:
            self._oParent.rename(sNewName)

    def remove_action(self, iIndex):
        oWidget = self._aActionWidgets.pop(iIndex)
        self.layout.remove_widget(oWidget)
        self._aActions.pop(iIndex)
        # Also update references in the widgets
        for oWidget in self._aActionWidgets:
            oWidget.update_index(iIndex)


class AddMaster(Popup):

    name = ObjectProperty(None)
    target = ObjectProperty(None)

    def __init__(self, oParent, bAdd, sOldName='', sOldTarget=''):
        super(AddMaster, self).__init__()
        self._oParent = oParent
        self._bAdd = bAdd
        self._sOldName = sOldName
        if sOldName:
            self.name.text = sOldName
        if sOldTarget:
            self.target.text = sOldTarget

    def done(self):
        sName = self.name.text.strip()
        sTarget = self.target.text.strip()
        self.name.focus = False
        self.target.focus = False
        if self._bAdd:
            self._oParent.add_master(sName, sTarget)
        else:
            self._oParent.update_master(self._sOldName, sName, sTarget)
        self.dismiss()

    def cancel(self):
        self.name.focus = False
        self.target.focus = False
        self.dismiss()


class MinionName(Popup):

    name = ObjectProperty(None)

    def __init__(self, oParent):
        super(MinionName, self).__init__()
        self._oParent = oParent

    def done(self):
        sName = self.name.text.strip()
        self.name.focus = False
        self._oParent.add_minion(sName)
        self.dismiss()

    def cancel(self):
        self.name.focus = False
        self.dismiss()


class MasterRow(BoxLayout):

    name = ObjectProperty(None)
    target = ObjectProperty(None)

    def __init__(self, sName, sTarget, oScreen, **kwargs):
        super(MasterRow, self).__init__(**kwargs)
        self.oScreen = oScreen
        self.name.text = sName
        if sTarget:
            self.target.text = 'targetting %s' % sTarget

    def get_target(self):
        if 'targetting' in self.target.text:
            return self.target.text.replace('targetting ', '', 1)
        return ''

    def set_target(self, sTarget):
        if sTarget:
            self.target.text = 'targetting %s' % sTarget
        else:
            self.target.text = ''


class MinionRow(BoxLayout):

    name = ObjectProperty(None)
    torpor = ObjectProperty(None)

    def __init__(self, sName, oScreen, **kwargs):
        super(MinionRow, self).__init__(**kwargs)
        self._sName = sName
        self.name.text = sName
        self.aActions = []
        self.bTorpor = False
        self.bBurnt = False
        self.oScreen = oScreen
        self.iTorporCount = 0

    def add_action(self, sAction, sResult):
        self.aActions.append('attempted to %s (%s)' % (sAction, sResult))

    def ask_action(self):
        oPopup = ActionChoice(self)
        oPopup.open()

    def get_name(self):
        return self._sName

    def rename(self, sNewName):
        sName = self.oScreen.update_minion(self._sName, sNewName)
        self._sName = sName
        self.name.text = sName

    def edit_minion(self):
        oPopup = EditMinion(self, self.aActions)
        oPopup.open()

    def burn(self):
        self.bBurnt = True
        self.oScreen._update_game()

    def get_actions(self):
        if not self.aActions:
            sResult = '%s (no actions).' % self._sName
        else:
            sResult = '%s (%s).' % (self._sName, ' & '.join(self.aActions))
        if self.iTorporCount > 1:
            sResult += ' Was sent to Torpor / Incapacitated (%d times)' % (
                self.iTorporCount)
        elif self.iTorporCount:
            sResult += ' Was sent to Torpor / Incapacitated.'
        if self.bBurnt:
            sResult += ' Was burnt.'
        elif self.bTorpor:
            sResult += ' In Torpor / Incapacitated.'
        else:
            sResult += ' Ready.'
        self.aActions = []
        self.iTorporCount = 0
        return sResult

    def is_burnt(self):
        return self.bBurnt

    def do_torpor(self):
        self.bTorpor = not self.bTorpor
        if self.bTorpor:
            self.iTorporCount += 1
            self.torpor.text = 'Rescue'
            self.name.color = [0.75, 0.15, 0.15, 1]
        else:
            self.torpor.text = 'Torpor'
            self.name.color = [1, 1, 1, 1]
        self.oScreen._update_game()


class PlayerScreen(RelativeLayout):

    game = ObjectProperty(None)
    player = ObjectProperty(None)
    turn_info = ObjectProperty(None)
    scroll = ObjectProperty(None)
    oust_but = ObjectProperty(None)

    def __init__(self, oGameWidget, sPlayer, sDeck):
        super(PlayerScreen, self).__init__()
        self.oGameWidget = oGameWidget
        self._sPlayer = sPlayer
        self._sDeck = sDeck
        self._bOusted = False
        self.iPool = 30
        self.aMinions = []
        self.aMasters = []
        self._aBurnt = set()
        self._oTimeLabel = Label(text='', markup=True)
        self._update_time_label(0)
        self.unhighlight_player()
        self._dMinions = {}
        self._dMasters = {}
        # We schedule this faster than the actual clock update
        # to reduce sampling issues
        Clock.schedule_interval(self._update_time_label, 0.5)

    def stop(self):
        """Cleanup"""
        Clock.unschedule(self._update_time_label)

    def ask_minion_name(self):
        if self._bOusted:
            return
        oPopup = MinionName(self)
        oPopup.open()

    def _get_unique_master_name(self, sName):
        sMaster = sName
        iCount = 1
        while sMaster in self.aMasters:
            sMaster = '%s (%d)' % (sName, iCount)
            iCount += 1
        return sMaster

    def _get_unique_minion_name(self, sName):
        iCount = 2
        sMinion = sName
        while sMinion in self._dMinions:
            sMinion = '%s (%d)' % (sName, iCount)
            iCount += 1
        return sMinion

    def add_minion(self, sName):
        if not sName:
            sName = 'Minion %d' % (len(self.aMinions) + 1)
        sMinion = self._get_unique_minion_name(sName)
        self.aMinions.append(sMinion)
        self._update_game()

    def get_minion(self, sMinion):
        return self._dMinions.get(sMinion, None)

    def get_master(self, sMaster):
        return self._dMasters.get(sMaster, None)

    def ask_master_details(self):
        if self._bOusted:
            return
        oPopup = AddMaster(self, True)
        oPopup.open()

    def add_master(self, sName, sTarget):
        if not sName:
            sName = 'Master %d' % (len(self.aMasters) + 1)
        sMaster = self._get_unique_master_name(sName)
        self.aMasters.append(sMaster)
        oWidget = MasterRow(sMaster, sTarget, self,
                            size_hint=(None, None))
        self._dMasters[sMaster] = oWidget
        self._update_game()

    def edit_master(self, sName):
        if self._bOusted or sName not in self._dMasters:
            return
        oWidget = self._dMasters[sName]
        sTarget = oWidget.get_target()
        oPopup = AddMaster(self, False, sName, sTarget)
        oPopup.open()

    def update_minion(self, sOldName, sNewName):
        if sNewName != sOldName:
            sName = self._get_unique_minion_name(sNewName)
            oWidget = self._dMinions[sOldName]
            iIndex = self.aMinions.index(sOldName)
            self.aMinions[iIndex] = sName
            del self._dMinions[sOldName]
            self._dMinions[sName] = oWidget
        else:
            sName = sOldName
        return sName

    def update_master(self, sOldName, sNewName, sNewTarget):
        oWidget = self._dMasters[sOldName]
        if sNewName != sOldName:
            del self._dMasters[sOldName]
            iIndex = self.aMasters.index(sOldName)
            sMaster = self._get_unique_master_name(sNewName)
            self._dMasters[sMaster] = oWidget
            self.aMasters[iIndex] = sMaster
            oWidget.name.text = sMaster
        if sNewTarget:
            oWidget.set_target(sNewTarget)
        else:
            oWidget.set_target('')

    def remove_master(self, sMaster):
        if sMaster in self.aMasters:
            del self._dMasters[sMaster]
            self.aMasters.remove(sMaster)
            self._update_game()

    def change_pool(self, iChg):
        if self._bOusted:
            return
        self.iPool += iChg
        self._update_game()

    def _update_game(self):
        for widget in self.game.children[:]:
            if not isinstance(widget, Button):
                self.game.remove_widget(widget)
            elif self._bOusted:
                widget.background_color = [0.5, 0.25, 0.25, 1]
        # Ousted players don't show any info about their ready region
        if self._bOusted:
            return
        oPool = Label(text="[color=ff0022]%d[/color]" % self.iPool,
                      markup=True, pos_hint={'right': 1, 'top': 0.98},
                      size_hint=(None, 0.02))
        self.game.add_widget(oPool)
        y = 0.95
        for sMaster in self.aMasters:
            if sMaster in self._dMasters:
                oWidget = self._dMasters[sMaster]
                oWidget.pos_hint = {'x': 0, 'top': y}
                y -= 0.035
                self.game.add_widget(oWidget)
        for sMinion in self.aMinions:
            if sMinion in self._dMinions:
                oMinion = self._dMinions[sMinion]
                if oMinion.is_burnt():
                    oMinion = None
                else:
                    oMinion.pos_hint = {'x': 0, 'top': y}
            else:
                oMinion = MinionRow(sMinion, self,
                                    pos_hint={'x': 0, 'top': y},
                                    size_hint=(None, None))
                self._dMinions[sMinion] = oMinion
            if oMinion:
                y -= 0.035
                self.game.add_widget(oMinion)

    def oust(self):
        if not self._bOusted:
            self.set_ousted()
            self.oGameWidget.oust()
        else:
            self.set_unousted()
            self.oGameWidget.unoust()

    def set_ousted(self):
        self._bOusted = True
        # This is ugly, but we need to hang onto a reference to avoid
        # self.scroll being remove by the gc
        self.oust_but.text = 'UnOust Player'

    def set_unousted(self):
        self._bOusted = False
        self.oust_but.text = 'Oust Player'
        self._update_game()

    def set_details(self, sPlayer, sDeck):
        self._sPlayer = sPlayer
        self._sDeck = sDeck

    def _remove_player_info(self):
        for label in self.player.children[:]:
            self.player.remove_widget(label)
        for label in self.turn_info.children[:]:
            self.turn_info.remove_widget(label)

    def _add_turn_info(self):
        label = self._get_round_label()
        self.turn_info.add_widget(label)
        self.turn_info.add_widget(self._oTimeLabel)

    def highlight_player(self):
        self._remove_player_info()
        if self._sDeck:
            label = Label(text="[b][color=00ffff]%s [i](playing %s)[/i]"
                          "[/color][/b]" % (escape_markup(self._sPlayer),
                                            escape_markup(self._sDeck)),
                          markup=True)
        else:
            label = Label(text="[b][color=00ffff]%s [i](unspecfied)"
                               "[/i][/color][/b] " % escape_markup(
                                   self._sPlayer),
                               markup=True)
        self.player.add_widget(label)
        self._add_turn_info()
        self._update_game()

    def get_turn_status(self):
        if self._sDeck:
            sInfo = '%s (playing %s)' % (self._sPlayer, self._sDeck)
        else:
            sInfo = '%s (playing unknown)' % (self._sPlayer)
        if self._bOusted:
            return '%s:\n      - ousted' % sInfo
        sHeader = '%s:\n      - %d pool' % (sInfo, self.iPool)
        aMasters = []
        for sMaster, oWidget in self._dMasters.iteritems():
            if oWidget.target.text:
                aMasters.append('%s (%s)' % (sMaster, oWidget.target.text))
            else:
                aMasters.append(sMaster)
        aMinions = []
        for sMinion, oWidget in self._dMinions.iteritems():
            if oWidget.is_burnt():
                if sMinion is self._aBurnt:
                    # Previously reported burn
                    continue
                else:
                    self._aBurnt.add(sMinion)
            sActions = oWidget.get_actions()
            aMinions.append('%s - {%s}' % (sMinion, sActions))
        if aMasters:
            sMasters = '      - masters:\n         - %s' % (
                '\n         - '.join(aMasters))
        else:
            sMasters = '      - masters:'
        if aMinions:
            sMinions = '      - minions:\n         - %s' % (
                '\n         - '.join(aMinions))
        else:
            sMinions = '      - minions:'
        return '\n'.join([sHeader, sMasters, sMinions])

    def unhighlight_player(self):
        self._remove_player_info()
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
                markup=True)
        else:
            label = Label(
                text="[b][color=%s]%s [i](unspecfied)%s"
                "[/i][/color][/b] " % (sColor, escape_markup(self._sPlayer),
                                       sOusted),
                markup=True)
        self.player.add_widget(label)
        self._add_turn_info()
        self.scroll.scroll_y = 1
        self._update_game()

    def _get_round_label(self):
        label = Label(text="[color=33ff33]Round %d.%d (%d players)[/color]"
                      % self.oGameWidget.get_round(), markup=True)
        return label

    def _update_time_label(self, dt):
        time_text = "[color=33ff33]Time: {:d}:{:02d}:{:02d}[/color]".format(
            *self.oGameWidget.get_time())
        self._oTimeLabel.text = time_text


class GameReportWidget(Carousel):

    def __init__(self, oApp):
        super(GameReportWidget, self).__init__()
        self.iCur = 0
        self.iScreen = 0
        self.aPlayers = []
        self.dDecks = {}
        self.dLog = {}
        self.iRound = 1
        self.aOusted = set()
        self.loop = True
        self._oApp = oApp
        self._oDate = datetime.datetime.utcnow()
        self._fTime = 0

    def start(self):
        """Start timers, etc."""
        Clock.schedule_interval(self._update_time, 1)

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

    def get_time(self):
        iTime = int(self._fTime + 0.5)
        iHours, iMinutes = iTime // 3600, iTime % 3600
        iMinutes, iSeconds = iMinutes // 60, iMinutes % 60
        return iHours, iMinutes, iSeconds

    def set_time(self, iHours, iMinutes, iSeconds):
        self._fTime = iHours * 3600.0 + iMinutes * 60.0 + iSeconds

    def _update_time(self, dt):
        self._fTime += dt

    def get_round_key(self):
        return '%02d.%d' % (self.iRound, self.iCur + 1)

    def get_rounds_list(self):
        aList = sorted(self.dLog)
        sCurRound = self.get_round_key()
        if sCurRound not in self.dLog:
            aList.append(sCurRound)
        return aList

    def next_turn(self):
        # Log the current turn and advance the turn
        sKey = self.get_round_key()
        self.step_current()
        if len(self.aOusted) == len(self.aPlayers):
            self.iCur = 0
        else:
            while self.iCur in self.aOusted:
                self.step_current()
        sTime = "%d:%02d:%02d" % self.get_time()
        aTurn = ['- elapsed time: %s' % sTime]
        for oScreen in self.slides:
            oScreen.unhighlight_player()
            aTurn.append(oScreen.get_turn_status())
        if self.iCur not in self.aOusted:
            self.slides[self.iCur].highlight_player()
        self.dLog[sKey] = aTurn
        # Save a temporary log of state at the start of the turn
        self.save_log(True)
        # We set things up so we can animate a scroll to the current player
        if self.index != self.iCur and self.parent:
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

    def unoust(self):
        self.aOusted.remove(self.index)
        self.update_details()

    def set_game_state(self, dOusted, dPool, dMasters, dMinions):
        for index, (slide, sPlayer) in enumerate(zip(self.slides,
                                                     self.aPlayers)):
            if dOusted[sPlayer]:
                self.aOusted.add(index)
                slide.iPool = 0
                slide.set_ousted()
                continue
            slide.iPool = dPool[sPlayer]
            aSeenMasters = set()
            for sMaster, sTarget in dMasters[sPlayer]:
                # FIXME: Check for master removal
                aSeenMasters.add(sMaster)
                if sMaster not in slide.aMasters:
                    slide.add_master(sMaster, sTarget)
                else:
                    oMaster = slide.get_master(sMaster)
                    oMaster.set_target(sTarget)
            for sCurMaster in slide.aMasters[:]:
                if sCurMaster not in aSeenMasters:
                    slide.remove_master(sCurMaster)
            for sMinion, sStatus in dMinions[sPlayer]:
                if sMinion not in slide.aMinions:
                    slide.add_minion(sMinion)
                oMinion = slide.get_minion(sMinion)
                if 'Was burnt.' in sStatus:
                    oMinion.burn()
                if 'Was sent to Torpor / Incapacitated (' in sStatus:
                    sTimes = sStatus.split('to Torpor / Incapacitated (')[1]
                    sTimes = sTimes.split(' times)')[0]
                    if 'Ready' in sStatus:
                        iCount = int(sTimes)
                    else:
                        # We only do a half cycle here
                        iCount = int(sTimes) - 1
                        oMinion.do_torpor()
                    for cycle in range(iCount):
                        # bounce minion
                        oMinion.do_torpor()
                        oMinion.do_torpor()
                elif 'Was sent to Torpor / Incapacitated' in sStatus:
                    oMinion.do_torpor()
                elif not 'Ready.' in sStatus:
                    oMinion.do_torpor()
                    # Unflag torpor this turn count
                    self.iTorporCount = 0
                elif oMinion.bTorpor and 'Ready.' in sStatus:
                    # Rescue minion
                    oMinion.do_torpor()
                if '(no actions)' in sStatus:
                    continue
                # Extract actions from the file
                for sCand in sStatus.split('attempted to')[1:]:
                    sAction, sRes = sCand.split('(', 1)
                    if 'unsucessfully' in sRes:
                        sRes = 'unsucessfully'
                    elif 'successfully' in sRes:
                        sRes = 'successfully'
                    elif 'was blocked' in sRes:
                        sRes = 'was blocked'
                    oMinion.add_action(sAction.strip(), sRes)
        self.update_details()

    def update_decks(self):
        self.parent.update_decks()

    def stop_game(self):
        Clock.unschedule(self._update_time)
        self.parent.stop_game()
        sKey = self.get_round_key()
        sTime = "%d:%02d:%02d" % self.get_time()
        aTurn = ['- elapsed time: %s' % sTime]
        for oScreen in self.slides:
            aTurn.append(oScreen.get_turn_status())
            oScreen.stop()
        self.dLog[sKey] = aTurn
        self.save_log()

    def get_log_for_turn(self, sRound):
        aLog = []
        aLog.append(sRound)
        for sPlayerInfo in self.dLog[sRound]:
            aLog.append('   %s' % sPlayerInfo)
        return '\n'.join(aLog)

    def get_log_file_name(self):
        sLogPath = self._oApp.config.get('vtes_report', 'logpath')
        sLogPrefix = self._oApp.config.get('vtes_report', 'logprefix')
        if not os.path.exists(sLogPath):
            os.makedirs(sLogPath)
        if not os.path.isdir(sLogPath):
            # FIXME: error popups and so forth
            return None, None
        sLogFile = "%s_%s.log" % (sLogPrefix,
                                  self._oDate.strftime('%Y-%m-%d_%H:%M'))
        sBackupLogFile = "%s_%s.old.log" % (sLogPrefix,
                                            self._oDate.strftime(
                                                '%Y-%m-%d_%H:%M'))
        sLogFile = os.path.join(sLogPath, sLogFile)
        sBackupLogFile = os.path.join(sLogPath, sBackupLogFile)
        return sLogFile, sBackupLogFile

    def save_log(self, bTemp=False):
        """Save the log"""
        sLogFile, sBackupLogFile = self.get_log_file_name()
        if not sLogFile:
            return
        if bTemp:
            sLogFile = sLogFile.replace('.log', '.temp.log')
        aLog = []
        for sRound in sorted(self.dLog):
            aLog.append(sRound)
            for sPlayerInfo in self.dLog[sRound]:
                aLog.append('   %s' % sPlayerInfo)
        if not bTemp:
            if os.path.exists(sLogFile):
                os.rename(sLogFile, sBackupLogFile)
        with open(sLogFile, 'w') as f:
            f.write('\n'.join(aLog))
            f.write('\n')


class PlayerSelectWidget(Widget):

    input_area = ObjectProperty(None)
    start_button = ObjectProperty(None)
    load_button = ObjectProperty(None)

    def __init__(self):
        super(PlayerSelectWidget, self).__init__()
        self._sMode = 'Start'
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
        if self.load_button not in self.children:
            self.add_widget(self.load_button)

    def set_resume_mode(self):
        self._sMode = 'Resume'
        self.start_button.text = self._sMode
        self.remove_widget(self.load_button)

    def set_info(self, aPlayers, dDecks):
        for sPlayer, oNameWidget, oDeckWidget in zip(aPlayers,
                                                     self._aNameWidgets,
                                                     self._aDeckWidgets):
            oNameWidget.text = sPlayer
            if dDecks[sPlayer]:
                oDeckWidget.text = dDecks[sPlayer]

    def ask_file(self):
        oPopup = LoadDialog(self.parent)
        oPopup.open()

    def start(self):
        aPlayers = []
        dDecks = {}
        for oPlayer, oDeck in zip(self._aNameWidgets, self._aDeckWidgets):
            if oPlayer.text.strip():
                aPlayers.append(oPlayer.text.strip())
                if oDeck.text.strip():
                    dDecks[oPlayer.text.strip()] = oDeck.text.strip()
        if aPlayers:
            if self._sMode == 'Start':
                self.parent.start_game(aPlayers, dDecks)
            else:
                self.parent.resume_game(aPlayers, dDecks)


class GameWidget(BoxLayout):

    def __init__(self):
        super(GameWidget, self).__init__()
        self.select = PlayerSelectWidget()
        self.game = None
        self._oApp = None
        self.add_widget(self.select)

    def set_app(self, oApp):
        self._oApp = oApp

    def start_game(self, aPlayers, dDecks):
        self.game = GameReportWidget(self._oApp)
        self.game.set_players(aPlayers)
        self.game.set_decks(dDecks)
        self.game.add_screens()
        self.remove_widget(self.select)
        self.add_widget(self.game)
        self.game.start()

    def stop_game(self):
        self.remove_widget(self.game)
        self.game = None
        self.select.set_start_mode()
        self.add_widget(self.select)

    def force_save(self):
        if self.game is not None:
            self.game.save_log()

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

    def load_log(self, filename):
        dTurns = {}
        sTurn = None
        aTurn = []
        with open(filename, 'rU') as f:
            # We need to find the last turn start
            for line in f.readlines():
                if not line.startswith(' '):
                    if sTurn:
                        dTurns[sTurn] = aTurn
                        aTurn = []
                    sTurn = line.strip()
                else:
                    aTurn.append(line.strip())
        if sTurn not in dTurns:
            dTurns[sTurn] = aTurn
        return dTurns, sTurn

    def load(self, filename):
        dTurns, sTurn = self.load_log(filename)
        self.load_game(dTurns, sTurn)
        self.game.start()

    def load_game(self, dTurns, sRound):
        self.game = GameReportWidget(self._oApp)
        for sTurn in sorted(dTurns):
            if sTurn <= sRound:
                self.load_turn(sTurn, dTurns[sTurn])
                if sTurn != sRound:
                    self.game.next_turn()
        self.remove_widget(self.select)
        self.game.index = self.game.iCur
        self.add_widget(self.game)

    def rollback(self):
        oPopup = RollbackDialog(self, self.game.get_rounds_list())
        oPopup.open()

    def rollback_to_round(self, sRound):
        self.game.save_log()
        sLogFile, _ = self.game.get_log_file_name()
        dTurns, _ = self.load_log(sLogFile)
        self.remove_widget(self.game)
        self.load_game(dTurns, sRound)

    def load_turn(self, sTurn, turn_data):
        iRound, iStep = [int(x) for x in sTurn.split('.')]
        self.game.iRound = iRound
        self.game.iCur = iStep - 1
        aPlayers = []
        dDecks = {}
        dMasters = {}
        dMinions = {}
        dPool = {}
        dOusted = {}
        sMode = None
        # Our file format isn't well designed, so this is horrible
        for line in turn_data:
            if line.startswith('- elapsed time'):
                # Extract the time and set it correctly
                _, sTime = line.split('- elapsed time:', 1)
                self.game.set_time(*[int(x) for x in sTime.split(':', 2)])
            elif not line.startswith('-'):
                sPlayer, sDeck = line.split('(playing')
                sDeck = sDeck[:-1]  # Drop trailing )
                aPlayers.append(sPlayer)
                dDecks[sPlayer] = sDeck
                dMasters.setdefault(sPlayer, [])
                dMinions.setdefault(sPlayer, [])
                sMode = None
                dOusted[sPlayer] = False
            elif 'pool' in line:
                sPool = line.replace('- ', '').replace(' pool', '')
                dPool[sPlayer] = int(sPool)
            elif line == '- ousted':
                dOusted[sPlayer] = True
            elif line == '- masters:':
                sMode = 'Masters'
            elif line == '- minions:':
                sMode = 'Minions'
            elif sMode == 'Masters' and line.startswith('- '):
                if '(targetting' in line:
                    sMaster, sTarget = line.split('(targetting')
                    sTarget = sTarget[:-1]
                    sMaster = sMaster[2:]
                else:
                    sMaster = line[2:]
                    sTarget = None
                dMasters[sPlayer].append((sMaster, sTarget))
            elif sMode == 'Minions' and line.startswith('- '):
                sMinion, sStatus = line.split(' - {', 1)
                sMinion = sMinion[2:]
                dMinions[sPlayer].append((sMinion, sStatus))
        if not self.game.aPlayers:
            self.select.set_info(aPlayers, dDecks)
            self.game.set_players(aPlayers)
            self.game.add_screens()
        self.game.set_decks(dDecks)
        self.game.set_game_state(dOusted, dPool, dMasters, dMinions)


class VTESGameApp(App):

    title = "VTES Game Reporter"

    def build(self):
        oMain = GameWidget()
        oMain.set_app(self)
        return oMain

    def on_stop(self):
        self.root.force_save()

    def on_pause(self):
        # Save the current log, in case we don't come back
        self.root.force_save()
        return True

    def build_config(self, config):
        config.setdefaults('vtes_report',
                           {'logpath': '/sdcard/VTES/',
                            'logprefix': 'VTES_Game'})

    def build_settings(self, settings):
        config_json = """[
            { "type": "title",
              "title": "VTES Game Reporting App"
            },

            { "type": "string",
              "title": "Log Path",
              "desc": "Path to save log files to",
              "section": "vtes_report",
              "key": "logpath"
            },

            {
              "type": "string",
              "title": "Prefix",
              "desc": "Prefix to use when generating log files",
              "section": "vtes_report",
              "key": "logprefix"
            }
            ]"""
        settings.add_json_panel("VTES Game Reporting",
                                self.config, data=config_json)


if __name__ == "__main__":
    VTESGameApp().run()
