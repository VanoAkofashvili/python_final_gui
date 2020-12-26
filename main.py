import sys
from PyQt5 import QtWidgets
import pandas as pd
from matplotlib import pyplot as plt
import collections
import threading
import numpy as np
import pathlib
from math import isnan
import pymongo
from UI.MainWindow import Ui_MainWindow
from database import MongoConnect


# pandas configuration
# pd.set_option("display.max_columns", 10)

class App(QtWidgets.QMainWindow, MongoConnect):
    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        MongoConnect.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # plt configuration
        plt.style.use('ggplot')
        # plt.style.use('fivethirtyeight')
        # plt.style.use('fast')
        #####################################

        self.begin_page()
        self.ui.comboBox.setEnabled(False)
        self.ui.comboBox.activated.connect(self.combobox_changes)

        # ყველას ჩატვირთვა
        self.ui.btn_upload.clicked.connect(self.load_all)
        # ყველას წაშლა
        self.ui.btn_delete_all.clicked.connect(self.delete_all)

        # პოპულარული ენები
        self.ui.btn_programming.clicked.connect(self.display_popular)
        # პოპულარული ბაზები
        self.ui.btn_dbs.clicked.connect(self.display_db)
        # ანაზღაურება ასაკის მიხედვით
        self.ui.btn_salary.clicked.connect(self.display_salary)

        # txt ფაილში ჩაწერა
        self.ui.btn_txt.clicked.connect(lambda: self.save_to_file('txt'))
        # csv ფაილში ჩაწერა
        self.ui.btn_csv.clicked.connect(lambda: self.save_to_file('csv'))
        # xlsx ფაილში ჩაწერა
        self.ui.btn_xlsx.clicked.connect(lambda: self.save_to_file('xlsx'))

        # Donate
        self.ui.btn_donate.clicked.connect(self.donate)

    def combobox_changes(self):
        chosen = self.ui.comboBox.currentText()
        if chosen == "ტექნოლოგიები":
            self.ui.middle_groupbox.setEnabled(True)
            self.ui.bottom_groupbox.setEnabled(False)
        elif chosen == "მონაცემები":
            self.ui.bottom_groupbox.setEnabled(True)
            self.ui.middle_groupbox.setEnabled(False)

    def donate(self):
        try:
            name = self.ui.text_name.toPlainText()
            surname = self.ui.text_surname.toPlainText()
            iban = self.ui.text_iban.toPlainText()
            money = self.ui.text_money.value()
            if name and surname and iban and money:
                dct = {
                    "From": f"{surname} {name}",
                    "To": "Akopashvili Vaniko",
                    "Iban": iban,
                    "Money": money
                }
                self.donate_coll.insert_one(dct)
                self.ui.error_msg.setText("გადახდა წარმატებით შესრულდა <3")
            else:
                raise ValueError("გთხოვთ შეავსოთ ყველა ველი")
        except ValueError as err:
            self.ui.error_msg.setText(str(err))

    # ფაილში შენახვა
    def save_to_file(self, file_ext):
        if file_ext == 'txt':
            t1 = threading.Thread(target=self.save_txt)
        elif file_ext == 'csv':
            t1 = threading.Thread(target=self.save_csv)
        elif file_ext == 'xlsx':
            t1 = threading.Thread(target=self.save_xlsx)
        else:
            raise RuntimeError("something went wrong")

        t1.start()
        t1.join()
        self.ui.error_msg.setText(f"Saved to {pathlib.Path().absolute()}/downloaded/data_{file_ext}.{file_ext}")

    # xlsx ფაილში გადაწერა
    def save_xlsx(self):
        df = pd.DataFrame(self.fetch_data(inc="", exc="_id"))
        df.to_excel('./downloaded/data_xlsx.xlsx')

    # csv ფაილში ჩაწერა
    def save_csv(self):
        df = pd.DataFrame(self.fetch_data(inc="", exc="_id"))
        df.to_csv('./downloaded/data_csv.csv')

    # txt ფაილში ჩაწერა
    def save_txt(self):
        df = pd.DataFrame(self.fetch_data(inc="", exc="_id"))
        np.savetxt(r'./downloaded/data_txt.txt', df.values, fmt='%s', encoding='utf-8')

    # get data from db
    def fetch_data(self, inc, exc):
        if inc:
            return self.coll.find({}, {inc: 1})
        else:
            return self.coll.find({}, {exc: 0})

    # ანაზღაურება ასაკის მიხედვით
    def display_salary(self):
        plt.title("ანაზღაურება ასაკის მიხედვით")
        plt.xlabel("ასაკი")
        plt.ylabel("ხელფასი (USD)")
        data = pd.DataFrame((self.coll.find({}, {"Age": 1, "ConvertedComp": 1})))
        ages_salary = []

        for row in data.itertuples():
            if isnan(row[2]) or isnan(row[3]) or row[2] > 70 or row[3] > 200000 or row[2] < 13:
                continue
            ages_salary.append((int(row[2]), round(row[3])))

        # sort by ages
        ages_salary = sorted(ages_salary, key=lambda x: x[0])

        # წლოვანების გაერთიანება და მათი ხელფასების საშუალოს აღება
        ages_sal_dict = dict()

        for row in ages_salary:
            lst = ages_sal_dict.get(row[0], [])
            lst.append(row[1])
            ages_sal_dict[row[0]] = lst

        avrg_sal = 0
        for key, val in ages_sal_dict.items():
            ages_sal_dict[key] = round(sum(val) / len(val))
            avrg_sal += ages_sal_dict[key]

        avrg_sal /= len(ages_sal_dict)

        plt.plot(ages_sal_dict.keys(), ages_sal_dict.values(), color='#444')
        plt.axhline(avrg_sal, color="#009eb3", linestyle='--')
        plt.fill_between(ages_sal_dict.keys(),
                         ages_sal_dict.values(),
                         avrg_sal,
                         interpolate=True,
                         alpha=0.25)

        plt.tight_layout()
        plt.show()

    # პოპულარული მონაცემთა ბაზები
    def display_db(self):
        data = self.fetch_data(inc="DatabaseWorkedWith", exc=None)
        db_counter = collections.Counter()
        for row in data:
            if isinstance(row["DatabaseWorkedWith"], float):
                continue
            dbs = row["DatabaseWorkedWith"].split(';')
            db_counter.update(dbs)

        dbs = []
        pop = []
        for db in db_counter.most_common(5):
            dbs.append(db[0])
            pop.append(db[1])

        plt.pie(pop, labels=dbs, wedgeprops={'edgecolor': 'black'}, shadow=True, startangle=90, autopct='%1.1f%%')
        plt.show()

    # პოპულარული ენები
    def display_popular(self):
        data = self.fetch_data(inc="LanguageWorkedWith", exc="")
        languages_counter = collections.Counter()
        for row in data:
            if isinstance(row["LanguageWorkedWith"], float):
                continue
            langs = row["LanguageWorkedWith"].split(';')
            languages_counter.update(langs)

        langs = []
        popul = []
        for lang in languages_counter.most_common():
            langs.append(lang[0])
            popul.append(lang[1])

        langs.reverse()
        popul.reverse()

        plt.barh(langs, popul)
        plt.title("ყველაზე პოპულარული ენები")
        plt.ylabel('პროგრამული ენები')
        plt.xlabel('დეველოპერების რაოდენობა')
        plt.tight_layout()
        plt.show()

    # პროგრამის საწყის მდგომარეობაში დაბრუნება
    def begin_page(self):
        self.ui.quantity.setText("სულ ბაზაშია 0 ჩანაწერი")
        # შეცდომის დამალვა
        self.ui.error_msg.hide()

        self.ui.middle_groupbox.setEnabled(False)
        self.ui.bottom_groupbox.setEnabled(False)

    def load_all(self):
        try:
            # ფაილის წაკითხვა
            l_data = pd.read_csv("./data/dt.csv")
        except:
            self.ui.error_msg.setText("დაფიქსირდა შეცდომა, სცადეთ ხელახლა")
        # ინდექსების შეცვლა
        l_data.set_index("Respondent", inplace=True)

        # მონაცემების ბაზაში ჩაწერა
        for _, row in l_data.iterrows():
            self.coll.insert_one(row.to_dict())

        # ბაზაში ჩანაწერების რაოდენობის გამოჩენა
        mongo_count = self.coll.estimated_document_count()

        self.ui.quantity.setText(f"სულ ბაზაშია: {mongo_count} ჩანაწერი")

        # შესაბამისი ღილაკების გააქტიურება
        text = self.ui.comboBox.currentText()
        if text == "ტექნოლოგიები":
            self.ui.middle_groupbox.setEnabled(True)
        elif text == "მონაცემები":
            pass
        else:
            self.show_message(msg="Something went wrong", error=True)

        self.show_message(msg="მონაცემები წარმატებით ჩაიტვირთა", error=False)

        # comboBox ის ჩართვა
        self.ui.comboBox.setEnabled(True)

    # ბაზის გასუფთავება
    def delete_all(self):
        self.coll.drop()
        self.show_message(msg="მონაცემები წარმატებით წაიშალა", error=False)
        self.begin_page()

    # alert მესიჯის გამოტანა
    def show_message(self, msg="", error=False):
        self.ui.error_msg.show()
        self.ui.error_msg.setText(msg)
        if error:
            styles = f"""
                font-size: 17px;
                color: white;
                background: #{"721c24"};
                border-radius: 10px;
            """
        else:
            styles = f"""
                font-size: 17px;
                color: white;
                background: #{"155724"};
                border-radius: 10px;
            """

        self.ui.error_msg.setStyleSheet(styles)


app = QtWidgets.QApplication([])
application = App()
application.show()
sys.exit(app.exec())
# # application.display_salary()
# application.display_salary()
