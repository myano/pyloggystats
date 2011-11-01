#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set fileencoding=UTF-8 :
"""
stats.py -- IRC Statistics Generator
Copyright 2011, Michael S. Yanovich

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.


This program generates statistics about an IRC channel when it was logged using
loggy.py -- http://inamidst.com/code/loggy.py (created by Sean B. Palmer)

The idea was inspired by the pisg project.
"""

LOGS_LOCATION = "/home/yano/yanovich.net/public/logs/"
FILE_EXTENSION = "txt"
CHANNEL = "#osu_osc"
USER = 'yano'

from StringIO import StringIO
import datetime
import random
import re
import os
import string
import recipe

class Stats():
    def __init__(self):
        self.lines_of_each_nick = {}
        #self.re_nick = re.compile(r"\s<([\S]+)>\s")
        self.re_newstyle = re.compile(r"^\d\d:\d\d:\d\d")
        self.re_oldstyle = re.compile(r"^\[\d\d:\d\d\]")
        self.re_oldstyle_topic = re.compile(r'^\[\d.*\sTopic\schanged.*:\s')
        self.nick_jpq = {}
        self.nick_mes = {}
        self.dict_of_topics = {}
        self.kicks = {}
        self.hours = {}
        self.hours_percent= {}
        self.days = 0
        self.user_hours = {}
        self.avg_chars = {}

    def load_lines(self):
        """
        This function loads data into several class-wide available variables
        for later computation.
        """
        for each in os.listdir(LOGS_LOCATION):
            self.days += 1
            if each.lower().endswith(FILE_EXTENSION):
                fn = open(LOGS_LOCATION + each, 'r')
                for eachline in fn:
                    eachline = eachline.lstrip()
                    ## loads regular text lines regardless of new or old
                    ## formatting
                    result_new = self.re_newstyle.findall(eachline)
                    result_old = self.re_oldstyle.findall(eachline)
                    if result_new:
                        ## NEW-STYLE
                        if eachline[9] == "*":
                            ## quit, part, joined, is nick change
                            if eachline[9:12] == "***":
                                ### quit, part or join
                                idx = eachline.find(" ", 13)
                                nick = eachline[13:idx].lower()
                                if nick.startswith("+") or nick.startswith("@"):
                                    nick = nick[1:]

                                if nick not in self.nick_jpq:
                                    self.nick_jpq[nick] = {"PART": 0, "JOIN": 0, "QUIT": 0}
                                if "has parted" in eachline:
                                    self.nick_jpq[nick]["PART"] += 1
                                elif "has joined" in eachline:
                                    self.nick_jpq[nick]["JOIN"] += 1
                                elif "has quit" in eachline:
                                    self.nick_jpq[nick]["QUIT"] += 1
                            else:
                                ### /me
                                ## eachline[9] == "*"
                                ## add to self.lines_of_each_nick
                                ## and have a var for how many me's
                                idx = eachline.find(" ", 11)
                                nick = eachline[11:idx].lower()
                                if nick.startswith("+") or nick.startswith("@"):
                                    nick = nick[1:]
                                tstamp = each[:-4] + " " + eachline[:8]
                                if nick not in self.lines_of_each_nick:
                                    self.lines_of_each_nick[nick] = {}
                                if tstamp not in self.lines_of_each_nick[nick]:
                                    self.lines_of_each_nick[nick][tstamp] = []
                                self.lines_of_each_nick[nick][tstamp] = eachline[11 + len(nick):-1]
                                if nick not in self.nick_mes:
                                    self.nick_mes[nick] = 0
                                self.nick_mes[nick] += 1

                        else:
                            ## regular text or topic
                            idx = eachline.find(">", 10)
                            nick = eachline[10:idx].lower()
                            if nick.startswith("+") or nick.startswith("@"):
                                nick = nick[1:]
                            if "freenode.net" in nick:
                                ## topic change or logger_osu joined
                                idx_tpc = eachline.find("is: ")
                                if idx_tpc > 0:
                                    ## topic change
                                    topic = eachline[idx_tpc + 4:-1]
                                    ky = each[:-4] + " " + eachline[:8]
                                    self.dict_of_topics[ky] = topic
                                else:
                                    ## List of users upon joining
                                    pass
                            else:
                                ## regular text
                                tstamp = each[:-4] + " " + eachline[:8]
                                if nick not in self.lines_of_each_nick:
                                    self.lines_of_each_nick[nick] = {}
                                if tstamp not in self.lines_of_each_nick[nick]:
                                    self.lines_of_each_nick[nick][tstamp] = []
                                self.lines_of_each_nick[nick][tstamp] = eachline[12 + len(nick):-1]

                    elif result_old:
                        ## OLD-STYLE
                        topic_changed = self.re_oldstyle_topic.findall(eachline)
                        joined_string = " joined " + CHANNEL + "."
                        part_string = " left " + CHANNEL
                        quit_string = " left irc:"
                        mode_change = CHANNEL + ": mode change"
                        if eachline[8] == "<":
                            ## regular line
                            idx = eachline.find(">", 8)
                            nick = eachline[9:idx].lower()
                            if nick.startswith("+") or nick.startswith("@"):
                                nick = nick[1:]
                            tstamp = each[:-4] + " " + eachline[1:6]
                            if nick not in self.lines_of_each_nick:
                                self.lines_of_each_nick[nick] = {}
                            if tstamp not in self.lines_of_each_nick[nick]:
                                self.lines_of_each_nick[nick][tstamp] = []
                            self.lines_of_each_nick[nick][tstamp] = eachline[11 + len(nick):-1]
                        elif eachline[8:15] == "Action:":
                            ## /me's
                            idx = eachline.find(" ", 16)
                            nick = eachline[16:idx].lower()
                            if nick.startswith("+") or nick.startswith("@"):
                                nick = nick[1:]
                            tstamp = each[:-4] + " " + eachline[1:6]
                            if nick not in self.lines_of_each_nick:
                                self.lines_of_each_nick[nick] = {}
                            if tstamp not in self.lines_of_each_nick[nick]:
                                    self.lines_of_each_nick[nick][tstamp] = []
                            self.lines_of_each_nick[nick][tstamp] = eachline[16 + len(nick):-1]
                            if nick not in self.nick_mes:
                                self.nick_mes[nick] = 0
                            self.nick_mes[nick] += 1
                        elif topic_changed:
                            ## topic is changed
                            idx = eachline.find(": ") + 2
                            topic = eachline[idx:-1]
                            ky = each[:-4] + " " + eachline[1:6]
                            self.dict_of_topics[ky] = topic
                        elif joined_string in eachline:
                            ## someone joined
                            idx = eachline.find(" ", 8)
                            nick = eachline[8:idx].lower()
                            if nick.startswith("+") or nick.startswith("@"):
                                nick = nick[1:]
                            if nick not in self.nick_jpq:
                                self.nick_jpq[nick] = {"PART": 0, "JOIN": 0, "QUIT": 0}
                            self.nick_jpq[nick]["JOIN"] += 1
                        elif part_string in eachline:
                            idx = eachline.find(" ", 8)
                            nick = eachline[8:idx].lower()
                            if nick.startswith("+") or nick.startswith("@"):
                                nick = nick[1:]
                            if nick not in self.nick_jpq:
                                self.nick_jpq[nick] = {"PART": 0, "JOIN": 0, "QUIT": 0}
                            self.nick_jpq[nick]["PART"] += 1
                        elif quit_string in eachline:
                            idx = eachline.find(" ", 8)
                            nick = eachline[8:idx].lower()
                            if nick.startswith("+") or nick.startswith("@"):
                                nick = nick[1:]
                            if nick not in self.nick_jpq:
                                self.nick_jpq[nick] = {"PART": 0, "JOIN": 0, "QUIT": 0}
                            self.nick_jpq[nick]["QUIT"] += 1
                        elif " kicked from %s by " % (CHANNEL) in eachline:
                            idx = eachline.find(" ", 8)
                            nick = eachline[8:idx].lower()
                            if nick.startswith("+") or nick.startswith("@"):
                                nick = nick[1:]
                            if nick not in self.kicks:
                                self.kicks[nick] = 0
                            self.kicks[nick] += 1
                        elif "returned to" in eachline or "got netsplit" in\
                        eachline or "---" in eachline or "Nick change" in\
                        eachline or "got lost in the net-split." in eachline\
                        or mode_change in eachline:
                            ## removed it to see what was left
                            pass
                        else:
                            #print eachline
                            pass
                    else:
                        ## blank line, do nothing
                        pass
                        #print eachline
                fn.close()

    def find_number_of_nicks(self):
        return len(self.lines_of_each_nick)

    def list_of_nicks(self):
        return self.lines_of_each_nick.keys()

    def number_of_lines_per_hour(self):
        #nicks = list_of_nicks
        for nick in self.lines_of_each_nick:
            for line in self.lines_of_each_nick[nick]:
                hour = int(line[11:13])
                if hour not in self.hours:
                    self.hours[hour] = 0
                self.hours[hour] += 1

    def sortdicts(self, x, y):
        return len(self.lines_of_each_nick[x]) - len(self.lines_of_each_nick[y])


    def high_score_cmp(self, x, y):
        if self.hours[x] < self.hours[y]:
            return 1
        elif self.hours[x] > self.hours[y]:
            return -1
        elif self.hours[x] == self.hours[y]:
            return 0

    def delete_existing_html(self):
        if os.path.isfile("index.html"):
            os.remove("index.html")

    def avg_chars_per_line_per_user(self):
        results = {}
        for nick in self.lines_of_each_nick:
            tmp = 0
            for line in self.lines_of_each_nick[nick]:
                tmp += len(self.lines_of_each_nick[nick][line])
            results[nick] = float(tmp) / len(self.lines_of_each_nick[nick])
        self.avg_chars = results

    def generate_lines_per_hour_per_user(self):
        for nick in self.lines_of_each_nick:
            if nick not in self.user_hours:
                self.user_hours[nick] = {}
            for line in self.lines_of_each_nick[nick]:
                hour = line[11:13]
                if hour not in self.user_hours[nick]:
                    self.user_hours[nick][hour] = 0
                self.user_hours[nick][hour] += 1
        #print self.user_hours

    def generate_webpage(self):
        self.delete_existing_html()
        page_file = open("index.html", "w")
        dt = recipe.doctype()
        page_file.write(str(dt))
        TITLE = CHANNEL + " IRC stats"
        css = '<link href ="style.css" rel="stylesheet" type="text/css" />\n'
        head = recipe.head(recipe.utf8() + recipe.title(TITLE) + css)

        ## CSS
        body = recipe.body()
        div1 = recipe.div("",Class="centered")

        ## beginning information
        div1 <= recipe.span("#osu_osc @ Freenode stats by %s" % (USER),Class="title")
        div1 <= recipe.br()
        ct = str(datetime.datetime.utcnow())
        div1 <= recipe.br()
        div1 <= "\nStatistics generated on %s UTC\n" % (ct)

        div1 <= recipe.br()
        div1 <= "During this %d-day reporting period, a total of <b>%d</b> different nicks were represented on %s." % (self.days, len(self.lines_of_each_nick), CHANNEL)
        div1 <= recipe.br()
        div1 <= recipe.br()
        tb1 = recipe.table(Class="tb4")
        tb1 <= recipe.tr(recipe.td('Most active times', Class='headertext'))
        div1 <= tb1

        ## Most Active Times
        tb2 = recipe.table(Class='tb2')
        tr2 = recipe.tr()
        q = -1
        TOTAL = 0
        for hour in self.hours:
            TOTAL += self.hours[hour]
        for hour in self.hours:
            q += 1
            if q < 6:
                colour = "blue"
            elif q < 12:
                colour = "green"
            elif q < 18:
                colour = "yellow"
            elif q < 24:
                colour = 'red'
            percent = float(self.hours[hour])/TOTAL*100.0
            height = 12.2 * percent
            alt = self.hours[hour]
            src = '{0:.2f}% <br><img src="images/{1}-v.png" style="width:15px; height: {2}px;" alt="{3}" title="{3}" />'.format(percent, colour, height, alt)
            td = recipe.td(src,Class="asmall2")
            tr2 <= td

        tb2 <= tr2

        high_ranking_list = sorted(self.hours, cmp=self.high_score_cmp)
        tr3 = recipe.tr()
        for x in range(0,24):
            if x == high_ranking_list[0]:
                td_temp = recipe.td("%d" % (x), Class='hirankc10center')
            else:
                td_temp = recipe.td("%d" % (x), Class="rankc10center")
            tr3 <= td_temp
        tb2 <= tr3
        div1 <= tb2
        ## END OF TABLE2

        tb3 = recipe.table(Class="tb3")
        tr3a = recipe.tr()
        tr3a <= recipe.td('<img src="images/blue-h.png" alt="0-5" class="bars" /> = 0-5',Class="asmall")
        tr3a <= recipe.td('<img src="images/green-h.png" alt="6-11" class="bars" /> = 6-11',Class="asmall")
        tr3a <= recipe.td('<img src="images/yellow-h.png" alt="12-17" class="bars" /> = 12-17',Class="asmall")
        tr3a <= recipe.td('<img src="images/red-h.png" alt="18-23" class="bars" /> = 18-23',Class="asmall")
        tb3 <= tr3a
        div1 <= tb3
        ## END OF TABLE3

        ## Most Active Nicks
        self.generate_lines_per_hour_per_user()

        div1 <= recipe.br()
        tb4 = recipe.table(Class="tb4")
        tr4a = recipe.tr(recipe.td("Most active nicks", Class="headertext"))
        tb4 <= tr4a
        div1 <= tb4
        div1 <= recipe.br()

        tb5 = recipe.table()
        tb5_tr1 = recipe.tr()
        tb5_tr1 <= recipe.td("&nbsp;")
        tb5_tr1 <= recipe.td("<strong>Nick</strong>", Class="tdtop")
        tb5_tr1 <= recipe.td("<strong>Number of lines</strong>",Class="tdtop")
        tb5_tr1 <= recipe.td("<strong>When?</strong>", Class="tdtop")
        tb5_tr1 <= recipe.td("<strong>Last Seen</strong>", Class="tdtop")
        tb5_tr1 <= recipe.td("<strong>Random Quote</strong>", Class="tdtop")
        tb5_tr1 <= recipe.td("<strong>Avg Char Per Line</strong>", Class="tdtop")
        tb5 <= tb5_tr1

        k = 0
        b = sorted(self.lines_of_each_nick, cmp=self.sortdicts)
        b.reverse()

        while k < 30:
            nick = b[k]
            num_of_lines = len(self.lines_of_each_nick[nick])
            ## find most recent line:
            a = sorted(self.lines_of_each_nick[nick].iterkeys())
            g = a[-1].split("-")
            year, month, day = int(g[0]), int(g[1]), int(g[2][:2])
            diff = datetime.datetime(year, month, day) - datetime.datetime.today()
            diff = str(diff).split(",")[0]
            diff = diff.replace("-1 day", "today")
            tb5_tr2 = recipe.tr()
            tb5_tr2 <= recipe.td("%d" % (k+1), Class="rankc")
            tb5_tr2 <= recipe.td("%s" % (nick), Class="c1")
            tb5_tr2 <= recipe.td("%d" % (num_of_lines), Class="bf")

            v = 0
            BLUE, GREEN, YELLOW, RED = 0, 0, 0, 0
            for hour in self.user_hours[nick]:
                hourint = int(hour)
                if 0 <= hourint <= 5:
                    BLUE += self.user_hours[nick][hour]
                elif 6 <= hourint <= 11:
                    GREEN += self.user_hours[nick][hour]
                elif 12 <= hourint <= 17:
                    YELLOW += self.user_hours[nick][hour]
                elif 18 <= hourint <= 23:
                    RED += self.user_hours[nick][hour]

            TOTAL = BLUE + GREEN + YELLOW + RED

            #print BLUE, GREEN, YELLOW, RED, TOTAL

            bpercent = float(BLUE)/TOTAL * 38
            gpercent = float(GREEN)/TOTAL * 38
            ypercent = float(YELLOW)/TOTAL * 38
            rpercent = float(RED)/TOTAL * 38

            ## chart column
            li_vars = {"blue": [bpercent, BLUE],
                    "green": [gpercent, GREEN],
                    "yellow": [ypercent, YELLOW],
                    "red": [rpercent, RED]
                    }
            tb5_td1 = recipe.td(Class="bb")
            for var in ["blue", "green", "yellow", "red"]:
                tb5_td1 <= '<img src="images/%s-h.png" width="%d" height="15" alt="%d" title="%d" />' % (var, li_vars[var][0], li_vars[var][0], li_vars[var][1])
            tb5_tr2 <= tb5_td1
            list_of_nick_lines = [self.lines_of_each_nick[nick][each] for each in \
                    self.lines_of_each_nick[nick]]
            tb5_tr2 <= recipe.td("%s" % (diff), Class="bf") ## last seen
            tb5_tr2 <= recipe.td("%s" % (random.choice(list_of_nick_lines)),Class = "bf") ## random quote
            tb5_tr2 <= recipe.td("%.2f" % (self.avg_chars[nick]), Class="bf")
            tb5 <= tb5_tr2

            k += 1
        div1 <= tb5

        spn = recipe.span(Class='small')
        spn <= recipe.br()
        spn <= "Stats generated by yano.\n"
        spn <= recipe.br()
        spn <= 'Themeing heavily borrowed from the pisg project: <a href="http://pisg.sourceforge.net/">pisg</a>.\n'
        spn <= recipe.br()
        spn <= 'pisg by <a href="http://mbrix.dk/" title="Go to the authors homepage" class="background">Morten Brix Pedersen</a> and others\n'
        div1 <= spn

        body <= div1
        body <= "\nâ\n"
        txt = recipe.html(head + body)
        output = StringIO()
        output.write(txt)
        page_file.write(output.getvalue())
        page_file.close()
        output.close()


stats = Stats()

def main():
    """
    Main function
    """
    stats.load_lines()
    stats.number_of_lines_per_hour()
    stats.avg_chars_per_line_per_user()
    #stats.percent_lines_per_hour()
    stats.generate_webpage()
    #print stats.avg_chars_per_line_per_user()

if __name__ == '__main__':
    main()
    print "Success, running main()!"
