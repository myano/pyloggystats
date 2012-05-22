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

import argparse
import datetime
import os
import random
import re
import recipe
import string
from StringIO import StringIO


class Stats():
    def __init__(self):
        self.lines_of_each_nick = dict()
        #self.re_nick = re.compile(r"\s<([\S]+)>\s")
        self.re_newstyle = re.compile(r"^\d\d:\d\d:\d\d")
        self.re_oldstyle = re.compile(r"^\[\d\d:\d\d\]")
        self.re_oldstyle_topic = re.compile(r'^\[\d.*\sTopic\schanged.*:\s')
        self.nick_jpq = dict()
        self.nick_mes = dict()
        self.dict_of_topics = dict()
        self.kicks = dict()
        self.hours = dict()
        for x in range(0, 24):
            self.hours[x] = 0
        self.hours_percent = dict()
        self.days = 0
        self.user_hours = dict()
        self.avg_chars = dict()
        self.words_per_nick = dict()
        self.most_used_words = dict()
        self.user = ""
        self.channel = ""
        self.file_extension = ""
        self.logs_location = ""
        self.stats_location = ""

    def check_for_logs(self):
        a = 0
        for each in os.listdir(self.logs_location):
            if each.lower().endswith(self.file_extension):
                a += 1
        if a == 0:
            return False
        else:
            return True

    def load_lines(self):
        """
        This function loads data into several class-wide available variables
        for later computation.
        """
        for each in os.listdir(self.logs_location):
            self.days += 1
            if each.lower().endswith(self.file_extension):
                try:
                    fn = open(self.logs_location + each, 'r')
                except:
                    print "Could not open", self.logs_location + each
                    continue
                for eachline in fn:
                    eachline = eachline.lstrip()
                    ## loads regular text lines regardless of new or old
                    ## formatting
                    result_new = self.re_newstyle.findall(eachline)
                    result_old = self.re_oldstyle.findall(eachline)
                    if result_new:
                        ## NEW-STYLE
                        ## http://go.osu.edu/loggy
                        if eachline[9] == "*":
                            ## quit, part, joined, is nick change
                            if eachline[9:12] == "***":
                                ### quit, part or join
                                idx = eachline.find(" ", 13)
                                nick = eachline[13:idx].lower()
                                if nick.startswith("+") \
                                        or nick.startswith("@"):
                                    nick = nick[1:]
                                if nick not in self.nick_jpq:
                                    self.nick_jpq[nick] = {"PART": 0,
                                            "JOIN": 0, "QUIT": 0}
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
                                if nick.startswith("+") \
                                        or nick.startswith("@"):
                                    nick = nick[1:]
                                tstamp = each[:-4] + " " + eachline[:8]
                                if nick not in self.lines_of_each_nick:
                                    self.lines_of_each_nick[nick] = dict()
                                if tstamp not in self.lines_of_each_nick[nick]:
                                    self.lines_of_each_nick[nick][tstamp] = \
                                            list()
                                self.lines_of_each_nick[nick][tstamp] = \
                                        eachline[11 + len(nick):-1]
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
                                    self.lines_of_each_nick[nick] = dict()
                                if tstamp not in self.lines_of_each_nick[nick]:
                                    self.lines_of_each_nick[nick][tstamp] = \
                                            list()
                                self.lines_of_each_nick[nick][tstamp] = \
                                        eachline[12 + len(nick):-1]

                    elif result_old:
                        ## OLD-STYLE -- eggdrop v1.6.19
                        topic_changed = \
                                self.re_oldstyle_topic.findall(eachline)
                        joined_string = " joined " + self.channel + "."
                        part_string = " left " + self.channel
                        quit_string = " left irc:"
                        mode_change = self.channel + ": mode change"
                        if eachline[8] == "<":
                            ## regular line
                            idx = eachline.find(">", 8)
                            nick = eachline[9:idx].lower()
                            if nick.startswith("+") or nick.startswith("@"):
                                nick = nick[1:]
                            tstamp = each[:-4] + " " + eachline[1:6]
                            if nick not in self.lines_of_each_nick:
                                self.lines_of_each_nick[nick] = dict()
                            if tstamp not in self.lines_of_each_nick[nick]:
                                self.lines_of_each_nick[nick][tstamp] = list()
                            self.lines_of_each_nick[nick][tstamp] = \
                                    eachline[11 + len(nick):-1]
                        elif eachline[8:15] == "Action:":
                            ## /me's
                            idx = eachline.find(" ", 16)
                            nick = eachline[16:idx].lower()
                            if nick.startswith("+") or nick.startswith("@"):
                                nick = nick[1:]
                            tstamp = each[:-4] + " " + eachline[1:6]
                            if nick not in self.lines_of_each_nick:
                                self.lines_of_each_nick[nick] = dict()
                            if tstamp not in self.lines_of_each_nick[nick]:
                                    self.lines_of_each_nick[nick][tstamp] = \
                                            list()
                            self.lines_of_each_nick[nick][tstamp] = \
                                    eachline[16 + len(nick):-1]
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
                                self.nick_jpq[nick] = {"PART": 0,
                                        "JOIN": 0, "QUIT": 0}
                            self.nick_jpq[nick]["JOIN"] += 1
                        elif part_string in eachline:
                            ## someone parted
                            idx = eachline.find(" ", 8)
                            nick = eachline[8:idx].lower()
                            if nick.startswith("+") or nick.startswith("@"):
                                nick = nick[1:]
                            if nick not in self.nick_jpq:
                                self.nick_jpq[nick] = {"PART": 0,
                                        "JOIN": 0, "QUIT": 0}
                            self.nick_jpq[nick]["PART"] += 1
                        elif quit_string in eachline:
                            ## someone quited
                            idx = eachline.find(" ", 8)
                            nick = eachline[8:idx].lower()
                            if nick.startswith("+") or nick.startswith("@"):
                                nick = nick[1:]
                            if nick not in self.nick_jpq:
                                self.nick_jpq[nick] = {"PART": 0,
                                        "JOIN": 0, "QUIT": 0}
                            self.nick_jpq[nick]["QUIT"] += 1
                        elif " kicked from %s by " % (self.channel) \
                                in eachline:
                            ## someone was kicked
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
                fn.close()

    def find_number_of_nicks(self):
        return len(self.lines_of_each_nick)

    def list_of_nicks(self):
        return self.lines_of_each_nick.keys()

    def number_of_lines_per_hour(self):
        for nick in self.lines_of_each_nick:
            for line in self.lines_of_each_nick[nick]:
                hour = int(line[11:13])
                if hour not in self.hours:
                    self.hours[hour] = 0
                self.hours[hour] += 1

    def sortdicts(self, x, y):
        return len(self.lines_of_each_nick[x]) - \
                len(self.lines_of_each_nick[y])

    def sortdicts_chars(self, x, y):
        return int(self.avg_chars[x] - self.avg_chars[y])

    def high_score_cmp(self, x, y):
        if self.hours[x] < self.hours[y]:
            return 1
        elif self.hours[x] > self.hours[y]:
            return -1
        elif self.hours[x] == self.hours[y]:
            return 0

    def delete_existing_html(self):
        loc = self.stats_location + "/index.html"
        if os.path.exists(loc):
            try:
                os.remove(loc)
            except:
                print "Unable to remove old index.html:", loc

    def avg_chars_per_line_per_user(self):
        results = dict()
        for nick in self.lines_of_each_nick:
            tmp = 0
            for line in self.lines_of_each_nick[nick]:
                tmp += len(self.lines_of_each_nick[nick][line])
            results[nick] = float(tmp) / len(self.lines_of_each_nick[nick])
        self.avg_chars = results

    def words_generator(self):
        re_word = re.compile(r"(\w+)")
        for nick in self.lines_of_each_nick:
            if nick not in self.words_per_nick:
                self.words_per_nick[nick] = 0
            for ts in self.lines_of_each_nick[nick]:
                temp = self.lines_of_each_nick[nick][ts]
                list_of_words = re_word.findall(temp)
                for word in list_of_words:
                    if word not in self.most_used_words:
                        self.most_used_words[word] = 0
                    self.most_used_words[word] += 1
                num_of_words = len(list_of_words)
                self.words_per_nick[nick] += num_of_words

    def generate_lines_per_hour_per_user(self):
        for nick in self.lines_of_each_nick:
            if nick not in self.user_hours:
                self.user_hours[nick] = dict()
            for line in self.lines_of_each_nick[nick]:
                hour = line[11:13]
                if hour not in self.user_hours[nick]:
                    self.user_hours[nick][hour] = 0
                self.user_hours[nick][hour] += 1

    def generate_webpage(self):
        self.delete_existing_html()
        loc = self.stats_location + "/index.html"
        self.words_generator()
        try:
            page_file = open(loc, "w")
        except:
            print "Could not open for writing:", loc
            return
        dt = recipe.doctype()
        page_file.write(str(dt))
        TITLE = self.channel + " IRC stats"
        css = '<link href ="style.css" rel="stylesheet" type="text/css" />\n'
        head = recipe.head(recipe.utf8() + recipe.title(TITLE) + css)

        ## CSS
        body = recipe.body()
        div1 = recipe.div("", Class="centered")

        ## beginning information
        div1 <= recipe.span("%s @ Freenode stats by %s" % (self.channel,
            self.user), Class="title")
        div1 <= recipe.br()
        ct = str(datetime.datetime.utcnow())
        div1 <= recipe.br()
        div1 <= "\nStatistics generated on %s UTC\n" % (ct)

        div1 <= recipe.br()
        div1 <= "During this %d-day reporting period,\
                a total of <b>%d</b> different nicks were represented on\
                %s." % (self.days, len(self.lines_of_each_nick), self.channel)
        div1 <= recipe.br()
        div1 <= recipe.br()
        tb1 = recipe.table(Class="tb4")
        tb1 <= recipe.tr(recipe.td('Most active times', Class='headertext'))
        div1 <= tb1

        ## Most Active Times
        tb2 = recipe.table(Class='tb2')
        tr2 = recipe.tr()
        # q = -1
        TOTAL = 0
        for hour in self.hours:
            TOTAL += self.hours[hour]
        for hour in self.hours:
            q = hour
            if q < 6:
                colour = "blue"
            elif q < 12:
                colour = "green"
            elif q < 18:
                colour = "yellow"
            elif q < 24:
                colour = "red"
            percent = float(self.hours[hour]) / TOTAL * 100.0
            height = 12.2 * percent
            alt = self.hours[hour]
            src = '{0:.2f}% <br><img src="images/{1}-v.png" style="width:15px;\
                    height: {2}px;" alt="{3}" title="{3}" />'.format(percent,
                            colour, height, alt)
            td = recipe.td(src, Class="asmall2")
            tr2 <= td

        tb2 <= tr2

        high_ranking_list = sorted(self.hours, cmp=self.high_score_cmp)
        tr3 = recipe.tr()
        for x in range(0, 24):
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
        tr3a <= recipe.td('<img src="images/blue-h.png" alt="0-5"\
                class="bars" /> = 0-5', Class="asmall")
        tr3a <= recipe.td('<img src="images/green-h.png" alt="6-11"\
                class="bars" /> = 6-11', Class="asmall")
        tr3a <= recipe.td('<img src="images/yellow-h.png" alt="12-17"\
                class="bars" /> = 12-17', Class="asmall")
        tr3a <= recipe.td('<img src="images/red-h.png" alt="18-23"\
                class="bars" /> = 18-23', Class="asmall")
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
        tb5_tr1 <= recipe.td("<strong>Number of lines</strong>", Class="tdtop")
        tb5_tr1 <= recipe.td("<strong>When?</strong>", Class="tdtop")
        tb5_tr1 <= recipe.td("<strong>Num of words</strong>", Class="tdtop")
        tb5_tr1 <= recipe.td("<strong>Last Seen</strong>", Class="tdtop")
        tb5_tr1 <= recipe.td("<strong>Random Quote</strong>", Class="tdtop")
        tb5_tr1 <= recipe.td("<strong>Avg Char Per Line</strong>",
                Class="tdtop")
        tb5 <= tb5_tr1

        k = 0
        b = sorted(self.lines_of_each_nick, cmp=self.sortdicts)
        b.reverse()

        while k < 25:
            nick = b[k]
            num_of_lines = len(self.lines_of_each_nick[nick])
            ## find most recent line:
            a = sorted(self.lines_of_each_nick[nick].iterkeys())
            g = a[-1].split("-")
            year, month, day = int(g[0]), int(g[1]), int(g[2][:2])
            diff = datetime.datetime(year, month,
                    day) - datetime.datetime.today()
            diff = str(diff).split(",")[0]
            diff = diff.replace("-1 day", "today")
            tb5_tr2 = recipe.tr()
            tb5_tr2 <= recipe.td("%d" % (k + 1), Class="rankc")
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

            bpercent = float(BLUE) / TOTAL * 38
            gpercent = float(GREEN) / TOTAL * 38
            ypercent = float(YELLOW) / TOTAL * 38
            rpercent = float(RED) / TOTAL * 38

            ## chart column
            li_vars = {"blue": [bpercent, BLUE],
                    "green": [gpercent, GREEN],
                    "yellow": [ypercent, YELLOW],
                    "red": [rpercent, RED]
                    }
            tb5_td1 = recipe.td(Class="bb")
            for var in ["blue", "green", "yellow", "red"]:
                tb5_td1 <= '<img src="images/%s-h.png" width="%d" height="15"\
                        alt="%d" title="%d" />' % (var, li_vars[var][0],
                                li_vars[var][0], li_vars[var][1])
            tb5_tr2 <= tb5_td1
            tb5_tr2 <= recipe.td(str(self.words_per_nick[nick]), Class="bf")
            list_of_nick_lines = [self.lines_of_each_nick[nick][each] for \
                    each in self.lines_of_each_nick[nick]]
            tb5_tr2 <= recipe.td("%s" % (diff), Class="bf")  # last seen
            tb5_tr2 <= recipe.td("%s" % (random.choice(list_of_nick_lines)),
                    Class="bf")  # random quote
            tb5_tr2 <= recipe.td("%.2f" % (self.avg_chars[nick]), Class="bf")
            tb5 <= tb5_tr2

            k += 1
        div1 <= tb5

        ## header for Nicks with longest lines
        div1 <= recipe.br()
        tb4 = recipe.table(Class="tb4")
        tr4a = recipe.tr(recipe.td("Nicks with Longest Lines",
            Class="headertext"))
        tb4 <= tr4a
        div1 <= tb4
        div1 <= recipe.br()

        ## ranking for avg_chars_per_user
        tb6 = recipe.table(Class="tb6")
        c = sorted(self.avg_chars, cmp=self.sortdicts_chars)
        c.reverse()
        j = 0

        tb6_tr1 = recipe.tr()
        tb6_tr1 <= recipe.td("&nbsp;")
        tb6_tr1 <= recipe.td("<strong>Nick</strong>", Class="tdtop")
        tb6_tr1 <= recipe.td("<strong>Avg Chars Per Line</strong>",
                Class="tdtop")
        tb6 <= tb6_tr1

        while j < 10:
            tr_temp = recipe.tr()
            nick = c[j]
            chars_per_line_per_user = self.avg_chars[nick]
            tr_temp <= recipe.td("%d" % (j + 1), Class="rankc")
            tr_temp <= recipe.td("%s" % (nick), Class="c1")
            tr_temp <= recipe.td("%d" % (chars_per_line_per_user), Class="bf")
            tb6 <= tr_temp
            j += 1
        ## END of TABLE6
        div1 <= tb6

        ## Header for Most Used Words
        div1 <= recipe.br()
        tb4 = recipe.table(Class="tb4")
        tr4a = recipe.tr(recipe.td("Most Used Words",
            Class="headertext"))
        tb4 <= tr4a
        div1 <= tb4
        div1 <= recipe.br()

        ## Ranking of most used words
        ## BEGINNING OF TABLE7
        tb7 = recipe.table(Class="tb7")
        muw = sorted(self.most_used_words, key=self.most_used_words.get)
        muw.reverse()
        m = 0
        tb7_tr1 = recipe.tr()
        tb7_tr1 <= recipe.td("&nbsp;")
        tb7_tr1 <= recipe.td("<strong>Word</strong>", Class="tdtop")
        tb7_tr1 <= recipe.td("<strong>Number of occuranes</strong>",
                Class="tdtop")
        tb7 <= tb7_tr1

        while m < 10:
            tr_temp = recipe.tr()
            word = muw[m]
            tr_temp <= recipe.td("%d" % (m + 1), Class="rankc")
            tr_temp <= recipe.td("%s" % (word), Class="c1")
            tr_temp <= recipe.td("%s" % (self.most_used_words[word]),
                    Class="bf")
            tb7 <= tr_temp
            m += 1

        ## END OF TABLE7
        div1 <= tb7

        spn = recipe.span(Class='small')
        spn <= recipe.br()
        spn <= "Stats generator by <a href='https://yanovich.net/'>yano</a>.\n"
        spn <= recipe.br()
        spn <= 'Theming heavily borrowed from the pisg project:\
                <a href="http://pisg.sourceforge.net/">pisg</a>.\n'
        spn <= recipe.br()
        spn <= 'pisg by <a href="http://mbrix.dk/" title="Go to the authors\
                homepage" class="background">Morten Brix Pedersen</a> and\
                others\n'
        div1 <= spn

        body <= div1
        body <= "\nâ\n"
        txt = recipe.html(head + body)
        output = StringIO()
        output.write(txt)
        page_file.write(output.getvalue())
        page_file.close()
        output.close()


def main():
    """
    Main function
    """

    ## parser code
    parser = argparse.ArgumentParser(description="The script makes an HTML\
            page from IRC logs.")
    parser.add_argument('-u', action='store', required=True, dest="user",
            help="specifies the user who is creating the logs.")
    parser.add_argument('-c', action='store', required=True, dest="channel",
            help="specifies the IRC channel of the logs.")
    parser.add_argument('-e', action='store', required=True,
            dest="file_extension", help="specifies the file extension of the\
                    IRC logs.")
    parser.add_argument('-l', action='store', required=True,
            dest="log_location", help="specifies the location of the IRC\
                    logs.")
    parser.add_argument('-s', action='store', dest="stats_location",
            help="specifies the location of the index.html")
    results = parser.parse_args()

    stats = Stats()
    stats.user = results.user
    stats.channel = results.channel
    stats.file_extension = results.file_extension
    stats.logs_location = results.log_location
    if results.stats_location:
        stats.stats_location = results.stats_location
    else:
        if not os.path.exists(stats.logs_location + "/stats/"):
            try:
                os.mkdir(stats.logs_location + "/stats/")
            except:
                print "Failed to create 'stats' folder, ", stats.logs_location
        stats.stats_location = stats.logs_location + "/stats/"

    ## start computing
    if stats.check_for_logs():
        stats.load_lines()
        stats.number_of_lines_per_hour()
        stats.avg_chars_per_line_per_user()
        stats.generate_webpage()

if __name__ == '__main__':
    main()
    #print "Success, running main()!"
