# encoding: utf-8
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import os

import bs4
from bs4 import BeautifulSoup as BeautifulSoup
import urllib.request

from github_issue import make_github_issue
from config import NEW_SUB_URL, KEYWORD_LIST, KEYWORD_EX_LIST, TARGET_TITLES


def main(mode):
    page = urllib.request.urlopen(NEW_SUB_URL)
    soup = BeautifulSoup(page, 'html.parser')
    content = soup.body.find("div", {'id': 'content'})

    issue_title = content.find("h3").text.split("(")[0].strip()

    dls = content.find_all("dl")
    target_soup = BeautifulSoup('', 'html.parser')
    new_tag = target_soup.new_tag('dl', id='articles')
    for dl in dls:
        h3_tag = dl.find('h3')
        for title in TARGET_TITLES:
            if h3_tag and title in h3_tag.text.strip():
                new_tag.append(dl)

    dt_list = new_tag.find_all("dt")
    dd_list = new_tag.find_all("dd")
    arxiv_base = "https://arxiv.org/abs/"

    assert len(dt_list) == len(dd_list)

    keyword_list = KEYWORD_LIST
    keyword_ex_list = KEYWORD_EX_LIST
    keyword_dict = []

    for i in range(len(dt_list)):
        paper = {}
        paper_number = dt_list[i].text.strip().split(":")[1][:11]  # [2].split(":")[-1]
        paper['main_page'] = arxiv_base + paper_number
        paper['pdf'] = arxiv_base.replace('abs', 'pdf') + paper_number

        paper['title'] = dd_list[i].find("div", {"class": "list-title mathjax"}).text.replace("Title:\n", "").strip()
        paper['authors'] = dd_list[i].find("div", {"class": "list-authors"}).text.replace("Authors:\n", "").replace(
            "\n", "").strip()
        paper['subjects'] = dd_list[i].find("div", {"class": "list-subjects"}).text.replace("Subjects: ", "").strip()
        paper['abstract'] = dd_list[i].find("p", {"class": "mathjax"}).text.replace("\n", " ").strip()

        includes = 0
        for keyword in keyword_list:
            if keyword.lower() in paper['abstract'].lower() or keyword.lower() in paper['title'].lower():
                includes = 1
        for keyword_ex in keyword_ex_list:
            if (keyword_ex.lower() in paper['abstract'].lower()) == 1:
                includes = 0
        if includes == 1:
            keyword_dict.append(paper)

    import datetime

    full_report = '# ' + issue_title + '\n'
    full_report = full_report + 'Auto update papers at about 2:30am UTC (10:30am Beijing time) every weekday.' + '\n'
    full_report = full_report + '\n\n'
    full_report = full_report + '阅读 `Usage.md`了解如何使用此repo实现个性化的Arxiv论文推送' + '\n\n'
    full_report = full_report + 'See `Usage.md` for instructions on how to personalize the repo. ' + '\n'
    full_report = full_report + '\n\n'
    full_report = full_report + 'Keyword list: ' + str(keyword_list) + '\n'
    full_report = full_report + '\n\n'
    full_report = full_report + 'Excluded: ' + str(keyword_ex_list) + '\n'
    full_report = full_report + '\n\n'

    full_report = full_report + '### Today: ' + str(len(keyword_dict)) + 'papers \n'

    if len(keyword_dict) == 0:
        full_report = full_report + 'There is no result \n'

    for paper in keyword_dict:
        report = (f"#### {paper['title']}\n"
                  f" - **Authors:** {paper['authors']}\n"
                  f" - **Subjects:** {paper['subjects']}\n"
                  f" - **Arxiv link:** {paper['main_page']}\n"
                  f" - **Pdf link:** {paper['pdf']}\n"
                  f" - **Abstract**\n {paper['abstract']}")
        full_report = full_report + report + '\n'

    full_report = full_report + '\n\n'
    full_report = full_report + 'by Zyzzyva0381 (Windy). ' + '\n'
    full_report = full_report + '\n\n'
    full_report = full_report + datetime.datetime.now().strftime("%Y-%m-%d") + '\n'

    if mode == "github":
        filename = './Arxiv_Daily_Notice/' + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + ('-Arxiv-Daily'
                                                                                                      '-Paper.md')
        filename_readme = './README.md'
        print(filename)
        with open(filename, 'w+') as f:
            f.write(full_report)

        with open(filename_readme, 'w+') as f:
            f.write(full_report)

        now = datetime.datetime.now()
        current_hour = now.hour
        if current_hour == 2:
            make_github_issue(title=issue_title, body=full_report, labels=keyword_list,
                              TOKEN=os.environ['TOKEN'])
        print("end")

    elif mode == "local":
        filename_test = './test.md'
        with open(filename_test, "w", encoding="utf8") as f:
            print(full_report, file=f)
        print(full_report)

    else:
        raise ValueError("mode must be either 'github' or 'local'")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Running on which device? ')
    parser.add_argument('-m', '--mode', help='if on GitHub, github', required=False, default='local')
    args = vars(parser.parse_args())
    main(args['mode'])
