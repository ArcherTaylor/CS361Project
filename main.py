import sys
import mysql.connector
from dotenv import load_dotenv
import os
import globals
from PyQt6 import QtWidgets, uic
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, Qt, pyqtSlot
import requests
import threading
import time
from portfolio_widget import Ui_Form as custom_portfolio_widget


from MainWindow import Ui_MainWindow

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PRIMARY_TABLE = os.getenv("DB_PRIMARY_TABLE")
DB_SECONDARY_TABLE = os.getenv("DB_SECONDARY_TABLE")
AVANTAGE_API_KEY = os.getenv("AVANTAGE_API_KEY")

class StockUpdater(QObject):
    stock_price_updated = pyqtSignal(str)

    def __init__(self):
        super().__init__()

    def start_updating(self):
        StockUpdaterThread = threading.Thread(target=self.update_stock_price)
        StockUpdaterThread.daemon = True
        StockUpdaterThread.start()
        
    def update_stock_price(self):
        while True:
            if globals.bs_ticker_viewing != "":
                price_response = requests.get(f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={globals.bs_ticker_viewing}&apikey={AVANTAGE_API_KEY}')
                price_data = price_response.json()['Global Quote']['05. price']

                self.stock_price_updated.emit(price_data)

            time.sleep(60) 

class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.stock_updater = StockUpdater()
        self.stock_updater.stock_price_updated.connect(self.stock_price_update)
        self.stock_updater.start_updating()

        self.stackedWidget.setCurrentIndex(0)
        self.goto_login_button.clicked.connect(self.LCA_page_login_button_clicked)
        self.goto_CA_button.clicked.connect(self.LCA_page_CA_button_clicked)
        self.login_page_button.clicked.connect(self.login_page_login_button_clicked)
        self.login_page_button_back.clicked.connect(self.LCA_page_back_button_clicked)
        self.CA_page_button.clicked.connect(self.CA_page_CA_button_clicked)
        self.CA_page_button_back.clicked.connect(self.LCA_page_back_button_clicked)
        self.welcome_buy_sell.clicked.connect(self.welcome_buy_sell_clicked)
        self.welcome_gen_reports.clicked.connect(self.welcome_gen_reports_clicked)
        self.welcome_view_portfolio.clicked.connect(self.welcome_view_portfolio_clicked)
        self.bs_submit_ticker.clicked.connect(self.bs_submit_clicked)
        self.bs_buy_button.clicked.connect(self.bs_buy_button_clicked)
        self.bs_sell_button.clicked.connect(self.bs_sell_button_clicked)
        self.bs_buy_cancel.clicked.connect(self.bs_buysell_cancel_clicked)
        self.bs_sell_cancel.clicked.connect(self.bs_buysell_cancel_clicked)
        self.bs_buy_confirm.clicked.connect(self.bs_buy_confirm_clicked)
        self.bs_sell_confirm.clicked.connect(self.bs_sell_confirm_clicked)
        self.bs_portfolio.clicked.connect(self.bs_portfolio_clicked)
        self.bs_bs.clicked.connect(self.bs_bs_clicked)
        self.bs_reports.clicked.connect(self.bs_reports_clicked)
        self.sell_sell_button.clicked.connect(self.sell_sell_clicked)
        self.sell_confirm_button.clicked.connect(self.sell_confirm_clicked)
        self.portfolio_reports.clicked.connect(self.portfolio_reports_clicked)
        self.portfolio_portfolio.clicked.connect(self.portfolio_portfolio_clicked)
        self.portfolio_bs.clicked.connect(self.portfolio_bs_clicked)

    def bs_reports_clicked(self):
        self.stackedWidget.setCurrentIndex(6)

    def portfolio_reports_clicked(self):
        self.stackedWidget.setCurrentIndex(6)
    
    def portfolio_portfolio_clicked(self):
        self.InitializePortfolioPage()

    def portfolio_bs_clicked(self):
        self.InitializeBuySellPage()
        self.stackedWidget.setCurrentIndex(4)

    def InitializeWelcomePage(self):
        self.welcome_page_welcome_label.setText(f"<html><head/><body><p align='center'><span style=' font-size:36pt; font-weight:700;'>Welcome, {globals.username}!</span></p></body></html>")

    def InitializeBuySellPage(self):
        self.bs_reset_ticker_box()
        globals.bs_ticker_viewing = ""
        globals.bs_ticker_viewing_price_now = ""
        globals.bs_ticker_viewing_quantity_owned = ""
        window.bs_stacked_widget.setCurrentIndex(0)

    def InitializePortfolioPage(self):

        for i in reversed(range(self.portfolio_verticalLayout.count())): 
            self.portfolio_verticalLayout.itemAt(i).widget().setParent(None)

        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        cursor = connection.cursor()

        find_query = "SELECT stock_ticker, stock_quantity, buying_price FROM user_stocks WHERE username = %s"
        cursor.execute(find_query, (globals.username,))
        found_info = cursor.fetchall()

        cursor.close()
        connection.close()

        for stocks in found_info:
            custom_widget = custom_portfolio_widget()
            custom_widget.setupUi(self)
            self.update_portfolio_widget_data(custom_widget, stocks[0], stocks[1], stocks[2])
            self.portfolio_verticalLayout.addWidget(custom_widget.portfolio_base)
            custom_widget.sellButton.clicked.connect(lambda _, t=stocks[0], q=stocks[1]: self.sell_button_clicked(t, q))

        self.portfolio_verticalLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.update_portfolio_value(found_info)

    def update_portfolio_value(self, database_info):
        portfolio_value = 0
        for stocks in database_info:
            price_response = requests.get(f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={str(stocks[0])}&apikey={AVANTAGE_API_KEY}')
            if price_response != {}:
                price_data = price_response.json()['Global Quote']['05. price']
                stock_valuation = round((float(price_data) * float(stocks[1])), 2)
                portfolio_value += stock_valuation
        self.portfolio_value_label.setText(f"<html><head/><body><p><span style=' font-size:48pt; font-weight:700;'>Current Portfolio Value: </span><span style=' font-size:48pt; font-weight:700; color:#85bb65;'>${portfolio_value}</span></p></body></html>")

    def sell_button_clicked(self, ticker, quantity):
        self.InitializeSellPage(ticker, quantity)
        self.stackedWidget.setCurrentIndex(7)

    def InitializeSellPage(self, ticker, quantity):
        self.sell_qty_widget.setCurrentIndex(0)
        self.sell_ticker_label.setText(f"<html><head/><body><p align='center'><span style=' font-size:36pt; font-weight:700;'>{ticker}</span></p></body></html>")
        self.sell_confirm_widget.hide()
        self.sell_notice_label.setText(f"<html><head/><body><p><span style=' font-weight:700;'>Please enter the quantity of shares you would like to sell. </span></p><p><span style=' font-weight:700;'>You have {quantity} shares available.</span></p></body></html>")
        globals.sell_ticker_viewing = ticker
        globals.sell_ticker_viewing_quantity = quantity

    def update_portfolio_widget_data(self, custom_widget, ticker, quantity, buying_price):
        custom_widget.ticker_label.setText(str(ticker))
        custom_widget.quantity_label.setText(str(quantity))
        custom_widget.buyingprice_label.setText(f"${str(buying_price)}")

        price_response = requests.get(f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker}&apikey={AVANTAGE_API_KEY}')
        price_data = price_response.json()['Global Quote']['05. price']
        custom_widget.currprice_label.setText(f"${str(price_data)}")
        

    def LCA_page_login_button_clicked(self):
        window.stackedWidget.setCurrentIndex(1)

    def LCA_page_CA_button_clicked(self):
        window.stackedWidget.setCurrentIndex(2)

    def login_page_login_button_clicked(self):
        self.login_notice_label.setText("")
        username_input = self.login_page_login_input.text()
        password_input = self.login_page_pw_input.text()

        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        cursor = connection.cursor()

        check_query = "SELECT * FROM users WHERE username = %s AND password = %s"
        check_values = (username_input, password_input)
        cursor.execute(check_query, check_values)
        check_result = cursor.fetchone()

        if(check_result):
            globals.username = username_input
            self.InitializeWelcomePage()
            window.stackedWidget.setCurrentIndex(3)
        else:
            self.login_notice_label.setText("You have entered an incorrect username/password!")
        cursor.close()
        connection.close()

    def CA_page_CA_button_clicked(self):
        self.CA_notice_label.setText("")
        username_input = self.CA_page_login_input.text()
        password_input = self.CA_page_pw_input.text()

        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        cursor = connection.cursor()

        check_query = f"SELECT * FROM {DB_PRIMARY_TABLE} WHERE username = %s"
        check_value = (username_input,)
        cursor.execute(check_query, check_value)
        check_result = cursor.fetchone()

        if(check_result):
            self.CA_notice_label.setText("An account already exists with this username!")
        else:
            insertion_query = f"INSERT INTO {DB_PRIMARY_TABLE} (username, password) VALUES (%s, %s)"
            insertion_values = (username_input, password_input)
            cursor.execute(insertion_query, insertion_values)
            connection.commit()
            globals.username = username_input
            self.InitializeWelcomePage()
            window.stackedWidget.setCurrentIndex(3)
        cursor.close()  
        connection.close()

    def LCA_page_back_button_clicked(self):
        window.stackedWidget.setCurrentIndex(0)

    def welcome_buy_sell_clicked(self):
        self.InitializeBuySellPage()
        window.stackedWidget.setCurrentIndex(4)

    def welcome_gen_reports_clicked(self):
        window.stackedWidget.setCurrentIndex(6)

    def welcome_view_portfolio_clicked(self):
        self.InitializePortfolioPage()
        window.stackedWidget.setCurrentIndex(5)

    def bs_reset_ticker_box(self):
        self.bs_info_ticker.setText("<html><head/><body><p align='center'><span style=' font-size:36pt; font-weight:700;'>Ticker</span></p></body></html>")
        self.bs_info_name.setText("<html><head/><body><p align='center'><span style=' font-size:18pt;'>Name of Company</span></p></body></html>")
        self.bs_info_price.setText("<html><head/><body><p align='center'><span style=' font-size:36pt; font-weight:700;'>$0.00</span></p></body></html>")
        self.bs_info_details.setText("<html><head/><body><p><span style=' font-size:14pt; font-weight:700;'>Exchange:</span></p><p><span style=' font-size:14pt; font-weight:700;'>Sector:</span></p><p><span style=' font-size:14pt; font-weight:700;'>52 Week High:</span></p><p><span style=' font-size:14pt; font-weight:700;'>52 Week Low: </span></p><p><br/></p><p><br/></p></body></html>")

    def bs_submit_clicked(self):
        self.bs_reset_ticker_box()
        ticker_input = self.bs_ticker_input.text().upper()
        if ticker_input == "":
            globals.bs_ticker_viewing = ""
            return

        information_response = requests.get(f'https://www.alphavantage.co/query?function=OVERVIEW&symbol={ticker_input}&apikey={AVANTAGE_API_KEY}')
        information_data = information_response.json()

        if information_data == {}:
            self.bs_ticker_input.setText("")
            self.bs_ticker_input.setPlaceholderText("Invalid ticker symbol!")
            self.bs_reset_ticker_box()
            return

        price_response = requests.get(f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={ticker_input}&apikey={AVANTAGE_API_KEY}')
        price_data = price_response.json()

        globals.bs_ticker_viewing = ticker_input
        globals.bs_ticker_viewing_price_now = price_data['Global Quote']['05. price']

        self.bs_info_ticker.setText(f"<html><head/><body><p align='center'><span style=' font-size:36pt; font-weight:700;'>{information_data['Symbol']}</span></p></body></html>")
        self.bs_info_name.setText(f"<html><head/><body><p align='center'><span style=' font-size:18pt;'>{information_data['Name']}</span></p></body></html>")
        self.bs_info_price.setText(f"<html><head/><body><p align='center'><span style=' font-size:36pt; font-weight:700;'>${price_data['Global Quote']['05. price']}</span></p></body></html>")
        self.bs_info_details.setText(f"<html><head/><body><p><span style=' font-size:14pt; font-weight:700;'>Exchange: {information_data['Exchange']}</span></p><p><span style=' font-size:14pt; font-weight:700;'>Sector: {information_data['Sector']}</span></p><p><span style=' font-size:14pt; font-weight:700;'>52 Week High: ${information_data['52WeekHigh']}</span></p><p><span style=' font-size:14pt; font-weight:700;'>52 Week Low: ${information_data['52WeekLow']}</span></p><p><br/></p><p><br/></p></body></html>")

    def bs_buy_button_clicked(self):
        if globals.bs_ticker_viewing == "":
            return
        window.bs_stacked_widget.setCurrentIndex(1)

    def bs_sell_button_clicked(self):
        if globals.bs_ticker_viewing == "":
            return
        quantity_owned = 0

        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        cursor = connection.cursor()

        quantity_query = "SELECT stock_quantity FROM user_stocks WHERE username = %s AND stock_ticker = %s"
        cursor.execute(quantity_query, (globals.username, globals.bs_ticker_viewing))
        quantity_result = cursor.fetchone()

        cursor.close()
        connection.close()

        if quantity_result is not None:
            quantity_owned = quantity_result[0]

        globals.bs_ticker_viewing_quantity_owned = quantity_owned

        self.bs_sell_quantity_label.setText(f"You currently have {quantity_owned} shares of {globals.bs_ticker_viewing} in your portfolio.")

        window.bs_stacked_widget.setCurrentIndex(2)

    def bs_buysell_cancel_clicked(self):
        window.bs_stacked_widget.setCurrentIndex(0)

    def bs_buy_confirm_clicked(self):
        quantity_input = int(self.bs_buy_quantity.text())
        if quantity_input <= 0:
            self.bs_buy_quantity.setPlaceholderText("Invalid quantity!")
            return
        
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        cursor = connection.cursor()

        query = f"INSERT INTO {DB_SECONDARY_TABLE} (username, stock_ticker, stock_quantity, buying_price) VALUES (%s, %s, %s, %s)"
        values = (globals.username, globals.bs_ticker_viewing, quantity_input, globals.bs_ticker_viewing_price_now)

        cursor.execute(query, values)
        connection.commit()
        cursor.close()
        connection.close()

        def timer_timeout_1():
            self.bs_processing_label.setText(f"<html><head/><body><p align='center'><span style=' font-size:14pt; font-weight:700;'>Order confirmed for {quantity_input} shares of {globals.bs_ticker_viewing}!</span></p></body></html>")
            timer.timeout.disconnect(timer_timeout_1)
            timer.timeout.connect(timer_timeout_2)
            timer.start(5000)

        def timer_timeout_2():
            window.bs_stacked_widget.setCurrentIndex(0)
            timer.stop()
            timer.timeout.disconnect(timer_timeout_2)

        window.bs_stacked_widget.setCurrentIndex(3)
        timer = QTimer()
        timer.timeout.connect(timer_timeout_1)
        timer.start(3000)

    def bs_sell_confirm_clicked(self):
        quantity_input = int(self.bs_sell_quantity.text())
        if(quantity_input > globals.bs_ticker_viewing_quantity_owned):
            self.bs_sell_quantity_label.setText(f"You have insufficient shares! You can sell up to {globals.bs_ticker_viewing_quantity_owned} of {globals.bs_ticker_viewing}!")
            return
        if quantity_input == 0:
            self.bs_sell_quantity_label.setText(f"You can not make a sale of 0 shares for {globals.bs_ticker_viewing}.")
            return

        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        cursor = connection.cursor()

        new_quantity = globals.bs_ticker_viewing_quantity_owned - quantity_input

        if new_quantity == 0:
            delete_query = "DELETE FROM user_stocks WHERE username = %s AND stock_ticker = %s"
            cursor.execute(delete_query, (globals.username, globals.bs_ticker_viewing))
        else:
            update_query = "UPDATE user_stocks SET stock_quantity = %s WHERE username = %s AND stock_ticker = %s"
            cursor.execute(update_query, (new_quantity, globals.username, globals.bs_ticker_viewing))

        connection.commit()
        cursor.close()  
        connection.close()
        
        def timer_timeout_1():
            self.bs_processing_label.setText(f"<html><head/><body><p align='center'><span style=' font-size:14pt; font-weight:700;'>Order confirmed for the sale of {quantity_input} shares of {globals.bs_ticker_viewing}!</span></p></body></html>")
            window.bs_stacked_widget.setCurrentIndex(3)
            timer.timeout.disconnect(timer_timeout_1)
            timer.timeout.connect(timer_timeout_2)
            timer.start(5000)

        def timer_timeout_2():
            window.bs_stacked_widget.setCurrentIndex(0)
            self.bs_processing_label.setText("<html><head/><body><p align='center'><span style=' font-size:24pt; font-weight:700;'>Processing Order</span></p></body></html>")
            timer.stop()
            timer.timeout.disconnect(timer_timeout_2)

        window.bs_stacked_widget.setCurrentIndex(3)
        timer = QTimer()
        timer.timeout.connect(timer_timeout_1)
        timer.start(3000)

    def stock_price_update(self, price_data):
        self.bs_info_price.setText(f"<html><head/><body><p align='center'><span style=' font-size:36pt; font-weight:700;'>${price_data}</span></p></body></html>")

    def bs_portfolio_clicked(self):
        self.InitializePortfolioPage()
        window.stackedWidget.setCurrentIndex(5)

    def bs_bs_clicked(self):
        self.InitializeBuySellPage()
        
    def sell_sell_clicked(self):
        if int(self.sell_qty_input.text()) > globals.sell_ticker_viewing_quantity:
            return
        price_response = requests.get(f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={globals.sell_ticker_viewing}&apikey={AVANTAGE_API_KEY}')
        price_data = price_response.json()['Global Quote']['05. price']
        valuation_calculation = float(price_data) * int(self.sell_qty_input.text())
        self.sell_confirm_notice.setText(f"<html><head/><body><p><span style=' font-weight:700;'>By hitting &quot;Confirm,&quot; you understand that are you selling </span></p><p><span style=' font-weight:700;'>{self.sell_qty_input.text()} shares of {globals.sell_ticker_viewing} in exchange for ${round(valuation_calculation, 2)}, before Capital Gains tax.</span></p></body></html>")
        self.sell_confirm_widget.show()

    def sell_confirm_clicked(self):
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        cursor = connection.cursor()

        new_quantity = globals.sell_ticker_viewing_quantity - int(self.sell_qty_input.text())
        if(new_quantity <= 0):
            deletion_query = "DELETE FROM user_stocks WHERE username = %s AND stock_ticker = %s"
            cursor.execute(deletion_query, (globals.username, globals.sell_ticker_viewing))
        else:
            update_query = "UPDATE user_stocks SET stock_quantity = %s WHERE username = %s AND stock_ticker = %s"
            cursor.execute(update_query, (new_quantity, globals.username, globals.sell_ticker_viewing))

        connection.commit()
        cursor.close()  
        connection.close()

        self.sell_confirm_complete_exit()

    def sell_confirm_complete_exit(self):
        self.sell_confirm_widget.hide()
        self.sell_qty_widget.setCurrentIndex(1)

        def timer_timeout_1():
            self.InitializePortfolioPage()
            self.stackedWidget.setCurrentIndex(5)
            timer.timeout.disconnect(timer_timeout_1)

        timer = QTimer()
        timer.timeout.connect(timer_timeout_1)
        timer.start(3000)

app = QtWidgets.QApplication(sys.argv)

window = MainWindow()
window.show()
app.exec()