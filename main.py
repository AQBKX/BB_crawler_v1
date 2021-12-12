import json
import re
import os.path
import tkinter.filedialog
from urllib.parse import parse_qsl
import requests
import time
from bs4 import BeautifulSoup
from tkinter import *
import urllib

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.55 Safari/537.36 Edg/96.0.1054.34',
    "Connection": "close"}
Host = "https://bb.btbu.edu.cn"
terms_select = {}
Session = requests.Session()


def init_userinfo():
    try:
        user_info = open("user_info.txt")
        user_data = user_info.read().splitlines()
        user_id = user_data[0]
        password = user_data[1]
        get_my_cookie(user_id, password)
    except IOError:
        info_error()
    except SyntaxError:
        info_error()
    except KeyError:
        info_error()
    except IndexError:
        info_error()
    else:
        user_info.close()


def info_error():
    print("请输入您的BB平台用户名和密码: ")
    user_id = input(" 用户名：")
    password = input(" 密 码：")
    user_info = open("user_info.txt", "w")
    user_info.write(str(user_id) + '\n' + str(password))
    user_info.close()
    init_userinfo()


def set_download_path():
    # 打开选择文件夹对话框
    try:
        download_path = open("user_info.txt", 'r').read().splitlines()[2]
    except IndexError:
        print("请选择课程文件下载路径：")
        root = Tk()
        root.withdraw()
        download_path = tkinter.filedialog.askdirectory()  # 获得选择好的文件夹
        root.destroy()
        if download_path == "":
            print('未选择路径，请重新开始并选择！！！\n')
            os.system('pause')
            os._exit(0)
        else:
            print("下载路径为：", download_path, '\n')
            upload_path = open("user_info.txt", 'a')
            upload_path.write('\n' + download_path)
            upload_path.close()
            return download_path + '/mySources'
    else:
        print("上次下载路径已加载： ", download_path, '\n')
        return download_path + '/mySources'


def get_my_cookie(user_id, password):
    login_data = {'user_id': user_id, 'password': password, 'action': 'login'}
    Session.get(append_host("/"), headers=headers)
    bb_login_ = Session.post(append_host("/webapps/login/"), headers=headers, data=login_data, allow_redirects=False)
    bb_login_ = Session.get(bb_login_.headers['Location'], headers=headers, allow_redirects=False)
    bb_login_ = Session.post(append_host(bb_login_.headers['Location']), headers=headers, allow_redirects=False)

    print(BeautifulSoup(bb_login_.text, 'html5lib').title.text.split('–')[0], "\n")
    # print("coolie ", "access!" if bb_login_.status_code == 200 else "error!")


def get_course_sources(sources_path):
    global terms_select
    tabAction_data = {'action': 'refreshAjaxModule', 'modId': '_23_1', 'tabId': '_2_1', 'tab_tab_group_id': '_2_1'}
    bb_course = Session.post(append_host("/webapps/portal/execute/tabs/tabAction"), headers=headers,
                             data=tabAction_data)
    soup_Course = BeautifulSoup(bb_course.text, 'html5lib')
    course_list_a = soup_Course.find_all('a', target="_top")
    course_term_set = set()
    for course_a in course_list_a:
        course_term_set.add(course_a.string[18:29])
    course_term_list = list(course_term_set)
    get_terms(course_term_list)
    for course_a in course_list_a:
        if terms_select[course_a.string[18:29]]:
            get_course_search(sources_path + '/' + get_good_path_module(course_a.string[30:]),
                              append_host(course_a['href']))


def get_course_search(course_path, href):
    launcher = Session.get(href, headers=headers, allow_redirects=False)
    launcher = Session.get(append_host(launcher.headers['Location']), headers=headers, allow_redirects=False)
    launcher = Session.get(append_host(launcher.headers['Location']), headers=headers, allow_redirects=False)
    launcher = Session.get(append_host(launcher.headers['Location']), headers=headers, allow_redirects=False)
    try:
        doc_href_of_soup_Course = BeautifulSoup(launcher.text, 'html5lib').find('span', title="课程文档").parent['href']
    except AttributeError:
        # print(os.path.basename(course_path))
        pass
    else:
        print(os.path.basename(course_path))
        get_document_href(course_path, doc_href_of_soup_Course)


def get_document_href(document_href_path, href):
    sources_a = BeautifulSoup(Session.get(append_host(href), headers=headers).text, 'html5lib')
    # BB平台文件资源获取
    for source_a in sources_a.find_all('img', alt="文件"):
        if source_a.parent.name == "a":
            documents_href = source_a.parent['href']
        else:
            documents_href = source_a.parent.find('a')['href']
        download(document_href_path, documents_href)
    # BB平台内容文件夹获取
    for source_a in sources_a.find_all('img', alt="内容文件夹"):
        folders_href = source_a.parent.find('a')['href']
        folders_name = trim([folder_name.contents for folder_name in source_a.parent.find('a').children][0][0])
        print("|-----", folders_name)
        get_document_href(document_href_path + '/' + get_good_path_module(folders_name), folders_href)


def download(download_path, href):
    document = Session.get(append_host(href), headers=headers, allow_redirects=False)
    document_name = os.path.basename(urllib.parse.unquote(document.headers['Location']))
    if not os.path.exists(download_path):
        os.makedirs(download_path)
    download_path = download_path + '/' + get_good_path_module(document_name)
    if os.path.exists(download_path):
        if os.path.isfile(download_path):
            print('|-     ' + document_name)
            pass
    else:
        dd = open(download_path, 'wb')
        dd.write(Session.get(append_host(document.headers['Location']), headers=headers).content)
        dd.close()
        print("|-新增", document_name)


def trim(s):
    if s == '':
        return s
    elif s[0] == ' ':
        return trim(s[1:])
    elif s[-1] == ' ':
        return trim(s[:-1])
    elif s[0] == ' ':
        return trim(s[1:])
    elif s[-1] == ' ':
        return trim(s[:-1])
    else:
        return s


def get_good_path_module(path_name):
    path_name = re.sub(r'[\\/:*?"<>|\r\n]+', "", path_name)
    path_name = trim(path_name)
    return path_name


def append_host(href="/"):
    href = trim(href)
    href = href if "https://bb.btbu.edu.cn" in href else Host + href
    return href


def get_terms(terms_list):
    global terms_select
    # 打开选择文件夹对话框
    try:
        terms = open("user_info.txt", 'r')
        terms_list = terms.read().splitlines()[3]
        terms_select = json.loads(terms_list)
        terms.close()
    except IndexError:
        get_usr_terms(terms_list)
    except TypeError:
        get_usr_terms(terms_list)
    except json.decoder.JSONDecodeError:
        print("文件错误")
        os.system("pause")
        exit()
    else:
        print("已选学期：", end='*')
        for term in terms_select:
            if terms_select[term]:
                print(term, end='*')
        print('\n')


def get_usr_terms(terms_list):
    global terms_select
    for term in terms_list:
        terms_select.setdefault(term, 0)
    root = Tk()
    Label(root, text="请输入关注的学期：").pack()
    for term in terms_select:
        terms_select[term] = IntVar()
        cb = Checkbutton(root, text=term, variable=terms_select[term], onvalue=1, offvalue=0)
        cb.pack()
    Button(root, text='确定', command=lambda: [cb_function(), root.destroy()]).pack()
    root.mainloop()


def cb_function():
    for term in terms_select:
        terms_select[term] = terms_select[term].get()
    terms_userinfo = open("user_info.txt", "a")
    terms_userinfo.write('\n' + json.dumps(terms_select))
    terms_userinfo.close()


def start():
    init_userinfo()
    path = set_download_path()
    get_course_sources(path)
    Session.close()
    print("\n****本次下载更新完成****")
    os.system('pause')


if __name__ == '__main__':
    start()
    # get_terms(['2021-2022-1', '2019-2020-2', '2019-2020-1', '2020-2021-2', '2020-2021-1'])
