import teamleaderclient as TL
from datetime import date, timedelta
from jinja2 import Environment, PackageLoader, select_autoescape
from dataclasses import dataclass,field
from typing import List, Union
import getpass
import re
import os
import subprocess

def get_time_trackings_for_day(d:date,session:TL.TLSession)->List[TL.TLTimeTracking]:
    user_id = session.get_user_id()
    filter = TL.TLFilter(user_id=user_id, _started_after=d, _ended_before=d + timedelta(days=1))
    number=1
    c = True
    trackings = []
    while c:
        try:
            page = TL.TLPage(10,number)
            body = TL.TLBody(filter=filter,page=page)
            timetracking = session.get_time_tracking(body=body)
            if isinstance(timetracking.data[0], TL.TLTimeTracking):
                trackings.extend(timetracking.data)
            else: 
                raise Exception(str(timetracking.data))
            number+=1
        except IndexError:
            c = False
        except Exception as e:
            print(timetracking.data)
            raise e
    return trackings

def removeurls(trackings:List[TL.TLTimeTracking])->List[TL.TLTimeTracking]:
    for tracking in trackings:
        tracking.description = re.sub(r"https{0,1}:\/\/([\w$-_.+!*'()]|\/)*\.([\w$-_.+!*'()]|\/)*", '', tracking.description, flags=re.MULTILINE).strip()
    return trackings

def dedupe(trackings:List[TL.TLTimeTracking])->List[TL.TLTimeTracking]: 
    d = {}
    for tracking in trackings:
        if d.get(tracking.description) is None:
            d[tracking.description] = tracking 
    return list(d.values())

def cencor(string:str)->str:
    length = len(string)
    return "".join([c if i < length/1.5 else "*" for i,c in enumerate(string)])

def enrichdescriptions(trackings:List[TL.TLTimeTracking])->List[TL.TLTimeTracking]: 
    for tracking in trackings:
        if tracking.subject is not None and tracking.subject.related_customer is not None:
            customer = cencor(f" Für: {tracking.subject.related_customer['description']}")
        else:
            customer = ""
        if tracking.invoiceable:
            meta = "Anpassung,"
        elif tracking.invoiceable == False and customer != "":
            meta = "Bugfix/Nichtregelzeit,"
        else:
            meta = "Tätigkeit,"
        tracking.description = f"{meta} {tracking.description} {customer}"
    return trackings

def get_correct_sdate(sdate:date)->date:
    if sdate.isocalendar()[2] == 1:
        return sdate
    else:
        return sdate - timedelta(days=sdate.isocalendar()[2] -1)
    

def get_correct_edate(edate:date)->date:
    if edate.isocalendar()[2] == 5:
        return edate
    else:
        return edate + timedelta(days=5-edate.isocalendar()[2])

def get_date_range(sdate:date,edate:date)->List[date]:
    return [sdate+timedelta(days=x) for x in range(((edate + timedelta(days=1))-sdate).days)]



def empty_list():
    return []

@dataclass
class Day:
    date: date
    session: TL.TLSession
    trackings: List[Union[TL.TLTimeTracking,None]] = field(init=False)
    name: str = field(init=False)
    num: int = field(init=False)
    num_month: int = field(init=False)
    month: str = field(init=False)
    def __post_init__(self):
        self.num = self.date.isocalendar()[2]
        self.num_month = self.date.strftime("%d")
        self.name = self.date.strftime("%A")
        self.month = self.date.strftime("%B")
        self.trackings = enrichdescriptions(dedupe(removeurls(get_time_trackings_for_day(self.date,self.session))))
@dataclass
class WorkWeek:
    start_date: date 
    end_date: date
    session: TL.TLSession
    days: List[Union[Day,None]] = field(init=False)
    year: int = field(init=False)
    num: int = field(init=False)
    def __post_init__(self):
        if (self.end_date - self.start_date).days > 4:
            raise Exception("Workweeks start- and enddate cant be more than 4 days appart")
        if (self.start_date.isocalendar()[2]) != 1:
            raise Exception("Workweeks startdate must be Monday")
        if (self.end_date.isocalendar()[2] != 5):
            raise Exception("Workweeks enddate must be Friday")
        self.num = self.start_date.isocalendar()[1]
        self.year = self.start_date.isocalendar()[0]
        days = get_date_range(self.start_date,self.end_date)
        self.days = [Day(d,self.session) for d in days]

def split_date_range_into_workweeks(dates:List[date],session:TL.TLSession)->List[WorkWeek]:
    if dates[0].isocalendar()[2] != 1:
        raise Exception("first day in list must be monday")
    weeks = []
    current_sdate = None
    for date in dates:
        if date.isocalendar()[2] == 1: 
            current_sdate = date
        if date.isocalendar()[2] == 5:
            weeks.append(WorkWeek(current_sdate,date,session))
            print("░░" ,end=" ", flush=True)
    return weeks

def main():
    parent_path = os.path.join('/',*__file__.split("/")[0:-2],"imager")
    print(parent_path)
    try: 
        subprocess.run(["yarn", "--cwd", parent_path ,"install"], check=True)
        subprocess.run(["npm", "--prefix", parent_path ,"install"], check=True)
    except Exception as e:
        print(e)
        exit(1)
    print("Environment setup:")
    startdate_year = int(input("Year to start at    >"))
    startdate_month =int(input("Month to start at   >"))
    startdate_day =  int(input("Day to start at     >"))
    enddate_year =   int(input("Year to end at      >"))
    enddate_month =  int(input("Month to end at     >"))
    enddate_day =    int(input("Day to end at       >"))
    email =              input("Teamleder email     >")
    pw =                 getpass.getpass("Teamleder password  >")
    session = TL.TLSession(email=email,password=pw)
    try:
        sdate = get_correct_sdate(date(startdate_year,startdate_month,startdate_day))
        edate = get_correct_edate(date(enddate_year, enddate_month, enddate_day))
        all_days = get_date_range(sdate, edate)
        workweeks = split_date_range_into_workweeks(all_days,session)
        env = Environment(
            loader=PackageLoader("reportgenerator"),
            autoescape=select_autoescape()
        )
        template = env.get_template("template.html")
        os.mkdir("out")
        os.mkdir("out/pdf")
    except Exception as e:
        print(e)
        exit(1)
    for week in workweeks:
        filename = f"out/{week.year}/{week.days[0].month}/{week.num}.html"
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        out = open(filename ,"a")
        result = template.render(week=week)
        out.write(result)
        print("██" ,end=" ",flush=True)
    subprocess.run(["node",os.path.join(parent_path,"index.js")],check=True)
    print("✓")
    exit(0)
