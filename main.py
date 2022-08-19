import json
import os
import webbrowser
from datetime import datetime, date

from splitwise import Splitwise
from dotenv import load_dotenv




def main():
    load_dotenv()
    s = get_splitwise()

    try:
        authenticate_from_saved_token(s)
    except:
        print("authenticate from saved session failed. Generating access token")
        generate_access_token(s)
        authenticate_from_saved_token(s)

    expenses = s.getExpenses(dated_after=datetime(2022, 8, 1))
    items = get_items(expenses, s)
    generate_qif(items)
    for item in items:
        print(item.get_date(), item.get_payee(), item.get_description(), item.get_value_to_user("Jack"), item.get_other_user("Jack"))

def get_items(expenses, s):
    items = []
    for expense in expenses:
        users = expense.getUsers()
        users_human = []
        for user in users:
            users_human.append(str(user.getFirstName()))
        repayments = expense.getRepayments()
        for repayment in repayments:
            items.append(SplitwiseItem(expense.getDate(), expense.getDescription(), expense.getCost(),
                                       s.getUser(repayment.getFromUser()).getFirstName(),
                                       s.getUser(repayment.getToUser()).getFirstName()))
    return items


def get_splitwise():
    CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
    CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")

    return Splitwise(CONSUMER_KEY, CONSUMER_SECRET)


def authenticate_from_saved_token(s):
    f = open('access_token.secret')
    access_token = json.load(f)
    s.setAccessToken(access_token)


def generate_access_token(s):
    url, oath_token_secret = s.getAuthorizeURL()
    webbrowser.open(url)

    authed_url = input("paste url")

    temp = authed_url.split("oauth_token=")
    temp2 = temp[1].split("&oauth_verifier=")
    token = temp2[0]
    verifier = temp2[1]

    access_token = s.getAccessToken(token, oath_token_secret, verifier)
    with open("access_token.secret", 'w') as outfile:
        json.dump(access_token, outfile)


class SplitwiseItem:
    def __init__(self, date_time, description, cost, paid_from, paid_to):
        self._date = date_time
        self._description = description
        self._cost = cost
        self._paid_to = paid_to
        self._paid_from = paid_from

    def get_date(self):
        date_split = self._date.split('-')
        year = int(date_split[0])
        month = int(date_split[1])
        day = int(date_split[2].split('T')[0])
        return date(year, month, day)

    def get_payee(self):
        return self._description.split("/")[0]

    def get_description(self):
        desc_split = self._description.split("/")
        if len(desc_split) > 1:
            return desc_split[1]
        else:
            return ""

    def get_value_to_user(self, user):
        if self._paid_to.lower() == user.lower():
            return float(self._cost)
        elif self._paid_from.lower() == user.lower():
            return float(self._cost) * -1
        else:
            print("given user: ", user, " is not involved in the transaction from ", self._paid_from, " to ",
                  self._paid_to)
            return 0

    def get_other_user(self, user):
        if self._paid_to.lower() == user.lower():
            return self._paid_from
        elif self._paid_from.lower() == user.lower():
            return self._paid_to
        else:
            print("given user: ", user, " is not involved in the transaction from ", self._paid_from, " to ",
                  self._paid_to)
            return ""

def generate_qif(items):
    with open("output.qif", "w") as f:
        f.write("!Type:Cash\n")
        for item in items:
            f.write("D"+str(item.get_date().month)+"/"+str(item.get_date().day)+"'"+str(item.get_date().year)+"\n")
            f.write("U"+str(item.get_value_to_user("Jack"))+"\n")
            f.write("T"+str(item.get_value_to_user("Jack"))+"\n")
            f.write("P"+str(item.get_payee())+"\n")
            f.write("M"+str(item.get_description())+" ("+str(item.get_other_user("Jack"))+")"+"\n")
            f.write("^\n")


main()
