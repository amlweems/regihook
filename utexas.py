from bs4 import BeautifulSoup
import requests
import datetime
import re

# Disable warnings for unverified connections
requests.packages.urllib3.disable_warnings()

class UTexasAuthenticationError(Exception): pass
class UTexasUnsupportedRequest(Exception): pass
class UTexasNonceNotFoundError(Exception): pass
class UTexasSemesterNotFound(Exception): pass

class UTexas:
    
    url = {
        "logon": "https://login.utexas.edu/openam/UI/Login",
        "registration": "https://utdirect.utexas.edu/registration/registration.WBX",
        "semester": "https://utdirect.utexas.edu/registration/chooseSemester.WBX",
        "email": "https://utdirect.utexas.edu/registration/confirmEmailAddress.WBX"
    }

    def __init__(self, auth):
        self.session = requests.session()
        self.session.verify = False
        self.auth = auth
        self.DEBUG = True

    def get_soup_text(self, soup, *args):
        return [m.text.lstrip().rstrip() for m in soup.find_all(*args)]

    def get_form_fields(self, form):
        data = {}
        for e in form.find_all('input'):
            name, value = e.get('name'), e.get('value')
            if name and value: data[name] = value
        return data

    def get_nonce(self, url):
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.content)
        nonce = soup.find_all('input', {'name':'s_nonce'})
        if nonce:
            self.nonce = nonce[0].get('value')

    def get_semester(self, season):
        url = self.url["semester"]
        resp = self.session.get(url)
        soup = BeautifulSoup(resp.content)
        options = []
        for form in soup.find_all('form'):
            options.append(self.get_form_fields(form))
        for option in options:
            if 'submit' not in option: continue
            if season.lower() in option['submit'].lower():
                self.semester = option
                return
        raise UTexasSemesterNotFound()

    def login(self):
        url = self.url["logon"]
        data = {
            "IDToken1": self.auth["username"],
            "IDToken2": self.auth["password"],
        }
        resp = self.session.post(url, data=data, verify=False)

        cookies = {"utlogin-prod": self.session.cookies.get('utlogin-prod')}
        self.session.cookies.clear()
        self.session.cookies = requests.cookies.cookiejar_from_dict(cookies)

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
        error += self.get_soup_text(soup, "form", {"action": "registrationAccessError.WBX"})
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

    def STUOF(self):
        """
        """
        data = {
            's_request': 'STUOF',
            'ack_dgre_plan': 'true'
        }
        resp = self.submit(self.url["email"], None, "GET")
        soup = BeautifulSoup(resp.content)
        for form in soup.find_all("form"):
            d = self.get_form_fields(form)
            if 'STUOF' in d.values():
                data.update(d)
        self.choose_semester()
        return self.submit(self.url["email"], data, "POST")

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
