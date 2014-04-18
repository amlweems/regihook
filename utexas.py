from bs4 import BeautifulSoup
import requests
import datetime
import re

class UTexasAuthenticationError(Exception): pass
class UTexasUnsupportedRequest(Exception): pass
class UTexasNonceNotFoundError(Exception): pass
class UTexasSemesterNotFound(Exception): pass

class UTexas:
    
    url = {
        "logon": "https://utdirect.utexas.edu/security-443/logon_check.logonform",
        "registration": "https://utdirect.utexas.edu/registration/registration.WBX",
        "semester": "https://utdirect.utexas.edu/registration/chooseSemester.WBX",
    }

    def __init__(self, auth):
        self.session = requests.session()
        self.session.verify = False
        self.auth = auth
        self.DEBUG = True

    def get_cdt(self):
        now = datetime.datetime.now()
        return now.strftime("%Y%m%d%H%M%S")

    def get_soup_text(self, soup, *args):
        return [m.text.lstrip().rstrip() for m in soup.find_all(*args)]

    def get_nonce(self, url):
        resp = self.session.get(url)
        nonce_re = re.findall('name="s_nonce" value="([^"]+)"', resp.text)
        if nonce_re:
            self.nonce = nonce_re[0]

    def get_semester(self, season):
        url = self.url["semester"]
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.content)
        options = []
        for form in soup.find_all('form'):
            data = {}
            for e in form.find_all('input'):
                data[e.get('name')] = e.get('value')
            options.append(data)
        for option in options:
            if 'submit' not in option: continue
            if season.lower() in option['submit'].lower():
                self.semester = option
                return
        raise UTexasSemesterNotFound()

    def login(self):
        url = self.url["logon"]
        data = {
            "CDT": self.get_cdt(),
            "LOGON": self.auth["username"],
            "PASSWORDS": self.auth["password"],
        }
        self.session.get(url, verify=False)
        resp = self.session.post(url, data=data, verify=False)
        authenticated = not(resp.cookies.get('FC') is None
            or resp.cookies.get('FC') is 'NONE')
        if not authenticated:
            raise UTexasAuthenticationError()
        return resp

    def submit(self, url, data, method="GET"):
        data['s_ccyys'] = self.semester['s_ccyys']
        data['s_nonce'] = self.nonce
        if method == "POST":
            resp = self.session.post(url, data=data)
        elif method == "GET":
            resp = self.session.get(url, params=data)
        else:
            raise UTexasUnsupportedRequest()
        soup = BeautifulSoup(resp.content)

        nonce = soup.find('input', {'name':'s_nonce'})
        if nonce: self.nonce = nonce.get("value")
        
        notif = self.get_soup_text(soup, "span", {"class": "notification"})
        error = self.get_soup_text(soup, "span", {"class": "error"})
        if self.DEBUG:
            for msg in notif: print(msg)
            for msg in error: print(msg)

        return not(bool(error))

    def STADD(self, unique_id):
        """Add
        """
        data = {
            's_request': 'STADD',
            's_unique_add': unique_id,
            's_submit': 'Submit',
        }
        self.choose_semester()
        return self.submit(self.url["registration"], data)

    def STAWL(self, unique_id, swap_id=None):
        """Add to waitlist
        """
        data = {
            's_request': 'STAWL',
            's_waitlist_unique': unique_id,
            's_waitlist_swap_unique': swap_id,
            's_submit': 'Submit',
        }
        self.choose_semester()
        return self.submit(self.url["registration"], data)

    def STDRP(self, unique_id):
        """Drop
        """
        data = {
            's_request': 'STDRP',
            's_unique_drop': unique_id,
            's_submit': 'Submit',
        }
        self.choose_semester()
        return self.submit(self.url["registration"], data)

    def STSWP(self, unique_id, drop_id):
        """Drop dependent upon add
        """
        data = {
            's_request': 'STDRP',
            's_swap_unique_add': unique_id,
            's_swap_unique_drop': drop_id,
            's_submit': 'Submit',
        }
        self.choose_semester()
        return self.submit(self.url["registration"], data)

    def STCPF(self, unique_id):
        """Change to pass/fail
        """
        data = {
            's_request': 'STDRP',
            's_unique_pass_fail': unique_id,
            's_submit': 'Submit',
        }
        self.choose_semester()
        return self.submit(self.url["registration"], data)

    def STGAR(self):
        """Get access to registration
        """
        data = {
            's_request': 'STGAR',
            's_submit': self.semester['submit'],
        }
        self.get_nonce(self.url["semester"])
        return self.submit(self.url["registration"], data, "POST")

    def choose_semester(self, semester="fall"):
        if "semester" not in self.__dict__:
            self.get_semester(semester)
        debug = self.DEBUG
        self.DEBUG = False
        ret = self.STGAR()
        self.DEBUG = debug
        return ret

    def register(self, unique_id):
        return self.STADD(unique_id)

    def waitlist(self, unique_id, swap_id=None):
        return self.STAWL(unique_id, swap_id)