import os
import json
import tempfile
from os import path
from cudatext import *
import cudatext_cmd as cmds
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

from cudax_lib import get_translation
_ = get_translation(__file__)  # I18N

PATH = tempfile.gettempdir() + os.sep + 'cudatext_gists'

class Command:
    def __init__(self):
        if os.path.exists(PATH) is False:
            try:
                os.mkdir(PATH)
            except OSError as err:
                msg_box("OS error: {0}".format(err), MB_OK)
                raise
        self.conf_file = ""

    def get_w_h(self):
        w_ = 600
        h_ = 600
        r = app_proc(PROC_COORD_MONITOR, 0)
        if r:
            w_ = (r[2]-r[0]) // 2
            h_ = (r[3]-r[1]) // 3

        return w_, h_

    def get_conf_file(self):
        return os.path.join(app_path(APP_DIR_SETTINGS), 'cuda_gists.json')

    def load_username(self):
        self.conf_file = self.get_conf_file()
        data_load_ = False
        if path.exists(self.conf_file):
            with open(self.conf_file, mode='r', encoding='utf-8') as fin:
                data_load_ = json.load(fin)['username']

        return data_load_

    def save_username(self, username_):
        self.conf_file = self.get_conf_file()
        data_ = {'username': username_}
        with open(self.conf_file, mode='w', encoding='utf-8') as fout:
            json.dump(data_, fout, indent=2)

    def load_gists(self, username_):
        response = None
        data_ = []
        ii = 2
        for i in range(1, ii):
            req = Request('https://api.github.com/users/' + username_ + '/gists?per_page=100&page=' + str(i))
            error = ''
            try:
                response = urlopen(req)
            except HTTPError as e:
                error = 'error code - ' + str(e.code)
            except URLError as e:
                error = 'reason - ' + str(e.reason)

            if error:
                msg_box(_('GitHub Gist: {}').format(error), MB_OK+MB_ICONERROR)
                return

            if response:
                gists = json.load(response)
                for i in gists:
                    desc_ = i['description'].replace('\n', ' ') if i['description'] else list(i['files'])[0]
                    preview_ = ', '.join(list(i['files']))
                    data_.append({'desc': desc_, 'preview': preview_, 'url': i['url']})
                if len(gists) == 100:
                    ii = ii + 1
            else:
                msg_box(_('GitHub Gist: empty response'), MB_OK+MB_ICONWARNING)
                return

        descs_ = ''
        if len(data_) > 0:
            for i in data_:
                for k, v in i.items():
                    if k == 'desc':
                        descs_ += v
                    if k == 'preview':
                        descs_ += '\t' + v
                descs_ += '\n'

        if len(descs_) > 0:
            w, h = self.get_w_h()
            res = dlg_menu(DMENU_LIST_ALT, descs_, 0, _('List of gists'), clip=CLIP_RIGHT, w=w, h=h)
            if res is not None:
                data_dict = json.load(urlopen(data_[res]['url']))['files']
                files_ = list(data_dict)
                for i in files_:
                    file_ = data_dict[i]['raw_url']
                    file_content_ = urlopen(file_).read().decode('utf-8')
                    tempfile_ = PATH + os.sep + i
                    open(tempfile_, 'w')
                    file_open(tempfile_)
                    ed.set_text_all(file_content_)
                    ed.save()
        else:
            msg_box(_('GitHub Gist: no gists found for username "{}"!').format(username_), MB_OK)
            return

        return data_

    def get_gists(self):
        get_username_ = self.load_username()
        if not get_username_:
            self.change_username()
        else:
            self.load_gists(get_username_)

    def change_username(self):
        username_ = dlg_input(_('Enter username on gist.github.com'), '')
        if username_:
            self.save_username(username_)
            self.load_gists(username_)
