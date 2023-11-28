import os
from tkinter import Y
import pandas
from typing import Union, List
from functools import partial
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtGui import QIcon, QCloseEvent, QKeyEvent, QResizeEvent
from PyQt5.QtWidgets import QMainWindow, QTabBar, QPushButton, QApplication, QWidget, QAction, QSplitter
from PyQt5.QtWidgets import QMenuBar, QMenu, QMessageBox
from yarl import URL
from webPageWidget2 import WebPageWidget, WebView
from CustomTabWidget import CustomTabWidget
from NavigationWidget import NavigationToolBar
from BookMarkWidget import BookMarkToolBar, BookMarkManager
from ConfigUtil import WebBrowserConfig
from DeveloperWidget import DeveloperWidget
from Common import makeQAction
from googleapiclient.discovery import build
import csv;import time
import sys
import requests
import re
import sys
import pprint
from selenium import webdriver
import time
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pynput import mouse

from selenium.webdriver.common.action_chains import ActionChains

#pip install google-api-python-client


class WebBrowserWindow(QMainWindow):
    _mb_show_navbar: QAction
    _mb_show_bookmark: QAction
    _mb_show_devtool: QAction

    def __init__(self, parent=None, init_url: Union[str, QUrl, None] = 'about:blank'):
        super().__init__(parent=parent)
        path_ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if os.getcwd() != path_:
            os.chdir(path_)

        self._bookMarkManager = BookMarkManager()
        self._config = WebBrowserConfig(self._bookMarkManager)


        self._navBar = NavigationToolBar(self)
        self._bookmarkBar = BookMarkToolBar(self._bookMarkManager, self)

        self._splitter = QSplitter(Qt.Horizontal, self)
        self._tabWidget = CustomTabWidget()
        self._devWidget = DeveloperWidget()

        self.initControl()
        self.initLayout()
        self._menuBar = QMenuBar(self)
        self.initMenuBar()
        self.setWindowTitle('DriveMange')
        self.setWindowIcon(QIcon('./Resource/application.ico'))
        if init_url is not None:
            if init_url == 'home':
                self.addWebPageTab(self._config.url_home)
            else:
                self.addWebPageTab(init_url)

    def release(self):
        self.closeWebPageAll()
        self._config.save_to_xml()

    def initLayout(self):
        self.setCentralWidget(self._splitter)
        self._splitter.addWidget(self._tabWidget)
        self._splitter.addWidget(self._devWidget)
        self._devWidget.hide()

    def initControl(self):
        self._splitter.setStyleSheet("QSplitter:handle:horizontal {background:rgb(204,206,219); margin:1px 1px}")

        self.addToolBar(Qt.TopToolBarArea, self._navBar)
        self._navBar.sig_navigate_url.connect(self.onNavBarNavitageUrl)
        self._navBar.sig_go_backward.connect(self.onNavBarGoBackward)
        self._navBar.sig_go_forward.connect(self.onNavBarGoForward)
        self._navBar.sig_reload.connect(self.onNavBarReload)
        self._navBar.sig_stop.connect(self.onNavBarStop)
        self._navBar.sig_go_home.connect(self.onNavBarGoHome)
        self._navBar.sig_toggle_bookmark.connect(self.onNavBarToggleBookmark)
        self._navBar.sig_go_check.connect(self.onNavBarCheck)

        self.addToolBarBreak(Qt.TopToolBarArea)
        self.addToolBar(Qt.TopToolBarArea, self._bookmarkBar)
        self._bookmarkBar.sig_navitage.connect(self.onNavBarNavitageUrl)

        self._tabWidget.sig_add_tab.connect(self.addWebPageTab)
        self._tabWidget.sig_new_window.connect(self.onTabNewWindow)
        self._tabWidget.sig_close.connect(self.onTabCloseView)
        self._tabWidget.sig_close_others.connect(self.onTabCloseViewOthers)
        self._tabWidget.sig_close_right.connect(self.onTabCloseRight)
        self._tabWidget.currentChanged.connect(self.onTabWidgetCurrentChanged)

        self._devWidget.sig_run_js.connect(self.runJavaScript)

    def initMenuBar(self):
        self.setMenuBar(self._menuBar)
        menuFile = QMenu('File', self._menuBar)
        self._menuBar.addAction(menuFile.menuAction())
        mb_close = makeQAction(parent=self, text='Close', triggered=self.close)
        menuFile.addAction(mb_close)

        menuView = QMenu('View', self._menuBar)
        self._menuBar.addAction(menuView.menuAction())
        self._mb_show_navbar = makeQAction(parent=self, text='Navigation Bar', checkable=True,
                                           triggered=self.toggleNavigationBar)
        self._mb_show_bookmark = makeQAction(parent=self, text='Bookmark Bar', checkable=True,
                                             triggered=self.toggleBookMarkBar)
        self._mb_show_devtool = makeQAction(parent=self, text='Dev Tool', checkable=True,
                                            triggered=self.toggleDevTool)
        menuView.addAction(self._mb_show_navbar)
        menuView.addAction(self._mb_show_bookmark)
        menuView.addSeparator()
        menuView.addAction(self._mb_show_devtool)
        menuView.aboutToShow.connect(self.onMenuViewAboutToShow)

        menuAbout = QMenu('About', self._menuBar)
        self._menuBar.addAction(menuAbout.menuAction())
        mb_about_page = makeQAction(parent=self, text='Page Info', triggered=self.showAboutPage)
        menuAbout.addAction(mb_about_page)

    def onMenuViewAboutToShow(self):
        self._mb_show_navbar.setChecked(self._navBar.isVisible())
        self._mb_show_bookmark.setChecked(self._bookmarkBar.isVisible())
        self._mb_show_devtool.setChecked(self._devWidget.isVisible())

    def onNavBarNavitageUrl(self, url: str):
        curwgt = self._tabWidget.currentWidget()
        if isinstance(curwgt, WebPageWidget):
            curwgt.load(url)

    def onNavBarGoBackward(self):
        curwgt = self._tabWidget.currentWidget()
        if isinstance(curwgt, WebPageWidget):
            curwgt.view().back()

    def onNavBarGoForward(self):
        curwgt = self._tabWidget.currentWidget()
        if isinstance(curwgt, WebPageWidget):
            curwgt.view().forward()

    def onNavBarReload(self):
        curwgt = self._tabWidget.currentWidget()
        if isinstance(curwgt, WebPageWidget):
            curwgt.view().reload()

    def onNavBarStop(self):
        curwgt = self._tabWidget.currentWidget()
        if isinstance(curwgt, WebPageWidget):
            curwgt.view().stop()

    def onNavBarGoHome(self):
        curwgt = self._tabWidget.currentWidget()
        if isinstance(curwgt, WebPageWidget):
            curwgt.load(self._config.url_home)

    def onNavBarToggleBookmark(self):
        curwgt = self._tabWidget.currentWidget()
        if isinstance(curwgt, WebPageWidget):
            url = curwgt.view().url().toString()
            if self._bookMarkManager.isExist(url):
                self._bookMarkManager.remove(url)
            else:
                url_icon = curwgt.view().iconUrl().toString()
                title = curwgt.view().title()
                self._bookMarkManager.add(url, title, url_icon)
            self.refreshNavBarState()
    
    def onNavBarCheck(self):
        import sys
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding = 'utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.detach(), encoding = 'utf-8')
        curwgt = self._tabWidget.currentWidget()
        page = curwgt.view().page()
        print(page.url().toString())
        if "https://www.youtube.com/watch?v=" in page.url().toString():
            a,b=page.url().toString().split('=')
            api_key = 'AIzaSyCME00vQ5XDIIW3-nEp9b8tnJCUEMWOImc'
            video_id = b
            replies = []
            f=open("./data/test.txt",'w',encoding='utf8')
            f.write("title\tcomment\n")
            f.close()
            re=[]
                # creating youtube resource object
            youtube = build('youtube', 'v3',
                            developerKey=api_key)
            
                # retrieve youtube video results
            video_response=youtube.commentThreads().list(
            part='snippet,replies',
            videoId=video_id
            ).execute()
            
                # iterate video response
            while video_response:
                    
                    # extracting required info
                    # from each result object 
                for item in video_response['items']:
                        
                        # Extracting comments
                    comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                        
                        # counting number of reply of comment
                    replycount = item['snippet']['totalReplyCount']
            
                        # if reply is there
                    if replycount>0:
                            
                            # iterate through all reply
                        for reply in item['replies']['comments']:
                                
                                # Extract reply
                            reply = reply['snippet']['textDisplay']
                                
                                # Store reply is list
                            replies.append(reply)
            
                        # print comment with list of reply
                    print(comment, replies, end = '\n\n')
                    re.append(comment)
                    
            
                        # empty reply list
                    replies = []
            
                    # Again repeat
                
                break
            for i in range(0,len(re)):
                f=open("./data/test.txt",'a',encoding='utf8')
                s=page.title()+"\t"+str(re[i])+"\n"
                f.write(s)
                f.close()
            a=os.system("python main2.py --model_type koelectra-base-v2 --model_name_or_path model --pred_dir preds --prediction_file prediction.csv --do_pred")
            buttonReply = QMessageBox.warning(
            self, '로딩중', "결과를 확인하시겠습니까?", 
            QMessageBox.Yes | QMessageBox.No
            )

            if buttonReply == QMessageBox.Yes:
                f=open('./preds/prediction.csv','r')
                l=[]
                lo=[0,0,0,0]
                rdr = csv.reader(f)
                for line in rdr:
                    l.append(line)
                f.close()
                for p in range(0,len(l)):
                    if l[p][1]=="gender":
                        lo[0]+=1
                        f=open("./data/test.txt",'a',encoding='utf8')
                        s=str(p+1)+"."+"성차별적 언행"+"\n"
                        f.write(s)
                        f.close()
                    elif l[p][1]=="hate":
                        lo[1]+=1
                        f=open("./data/test.txt",'a',encoding='utf8')
                        s=str(p+1)+"."+"욕설"+"\n"
                        f.write(s)
                        f.close()
                    elif l[p][1]=="offensive":
                        lo[2]+=1
                        f=open("./data/test.txt",'a',encoding='utf8')
                        s=str(p+1)+"."+"공격성 언행"+"\n"
                        f.write(s)
                        f.close()
                    elif l[p][1] == "other":
                        lo[3]+=1
                        f=open("./data/test.txt",'a',encoding='utf8')
                        s=str(p+1)+"."+"기타"+"\n"
                        f.write(s)
                        f.close()
                        
                buttonReply2 = QMessageBox.warning(
                    self,"결과","성차별적 언행 : "+str(lo[0])+"\n욕설 : "+str(lo[1])+"\n공격적 언행 : "+str(lo[2])+"\n기타 : "+str(lo[3])+"\n계속하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No
                    )
                if buttonReply2 == QMessageBox.No:
                    curwgt = self._tabWidget.currentWidget()
                    curwgt.view().back()
            elif buttonReply == QMessageBox.No:
                print('Save clicked.')
        elif "https://n.news.naver.com/mnews/" in page.url().toString():
            options = webdriver.ChromeOptions() # 크롬 옵션 객체 생성
            options.add_argument('headless') # headless 모드 설정
            options.add_argument("window-size=1920x1080") # 화면크기(전체화면)
            options.add_argument("disable-gpu") 
            options.add_argument("disable-infobars")
            options.add_argument("--disable-extensions")
            prefs = {'profile.default_content_setting_values': {'cookies' : 2, 'images': 2, 'plugins' : 2, 'popups': 2, 'geolocation': 2, 'notifications' : 2, 'auto_select_certificate': 2, 'fullscreen' : 2, 'mouselock' : 2, 'mixed_script': 2, 'media_stream' : 2, 'media_stream_mic' : 2, 'media_stream_camera': 2, 'protocol_handlers' : 2, 'ppapi_broker' : 2, 'automatic_downloads': 2, 'midi_sysex' : 2, 'push_messaging' : 2, 'ssl_cert_decisions': 2, 'metro_switch_to_desktop' : 2, 'protected_media_identifier': 2, 'app_banner': 2, 'site_engagement' : 2, 'durable_storage' : 2}}   
            options.add_experimental_option('prefs', prefs)
            f=open("./data/test.txt",'w',encoding='utf8')
            f.write("title\tcomment\n")
            url = page.url().toString()
 
            #웹 드라이버
            driver = webdriver.Chrome('./chromedriver.exe',options=options)
            driver.implicitly_wait(30)
            driver.get(url)
            
            #네이버의 경우, 클린봇으로 추출이 안되는게 있다, 클린봇 옵션 해제 후 추출해주도록 한다.
            cleanbot = driver.find_element(By.CSS_SELECTOR,'a.u_cbox_cleanbot_setbutton')
            cleanbot.click()
            time.sleep(1)
            cleanbot_disable = driver.find_element(By.XPATH,"//input[@id='cleanbot_dialog_checkbox_cbox_module']")
            cleanbot_disable.click()
            time.sleep(1)
            cleanbot_confirm = driver.find_element(By.XPATH,"//button[@class='u_cbox_layer_cleanbot2_extrabtn']")
            cleanbot_confirm.click()
            time.sleep(1)
            
            #더보기 계속 클릭하기
            while True:
                try:
                    btn_more = driver.find_element(By.CSS_SELECTOR,'span.u_cbox_in_view_comment')
                    btn_more.click()
                    # time.sleep(1)
                except:
                    break
        
            
            
            #댓글추출
            contents = driver.find_elements(By.CSS_SELECTOR,'span.u_cbox_contents')
            cnt = 1
            for content in contents:
                f=open("./data/test.txt",'a',encoding='utf8')
                s=page.title()+"\t"+content.text+"\n"
                f.write(s)
                f.close()
                cnt+=1
            a=os.system("python main2.py --model_type koelectra-base-v2 --model_name_or_path model --pred_dir preds --prediction_file prediction.csv --do_pred")
            buttonReply = QMessageBox.warning(
            self, '로딩중', "결과를 확인하시겠습니까?", 
            QMessageBox.Yes | QMessageBox.No
            )

            if buttonReply == QMessageBox.Yes:
                f=open('./preds/prediction.csv','r')
                l=[]
                lo=[0,0,0,0]
                rdr = csv.reader(f)
                for line in rdr:
                    l.append(line)
                f.close()
                for p in range(0,len(l)):
                    if l[p][1]=="gender":
                        lo[0]+=1
                        f=open("./data/test.txt",'a',encoding='utf8')
                        s=str(p+1)+"."+"성차별적 언행"+"\n"
                        f.write(s)
                        f.close()
                    elif l[p][1]=="hate":
                        lo[1]+=1
                        f=open("./data/test.txt",'a',encoding='utf8')
                        s=str(p+1)+"."+"욕설"+"\n"
                        f.write(s)
                        f.close()
                    elif l[p][1]=="offensive":
                        lo[2]+=1
                        f=open("./data/test.txt",'a',encoding='utf8')
                        s=str(p+1)+"."+"공격성 언행"+"\n"
                        f.write(s)
                        f.close()
                    elif l[p][1] == "other":
                        lo[3]+=1
                        f=open("./data/test.txt",'a',encoding='utf8')
                        s=str(p+1)+"."+"기타"+"\n"
                        f.write(s)
                        f.close()
                buttonReply2 = QMessageBox.warning(
                    self,"결과","성차별적 언행 : "+str(lo[0])+"\n욕설 : "+str(lo[1])+"\n공격적 언행 : "+str(lo[2])+"\n기타 : "+str(lo[3])+"\n계속하시겠습니까?",
                    QMessageBox.Yes | QMessageBox.No
                    )
                if buttonReply2 == QMessageBox.No:
                    curwgt = self._tabWidget.currentWidget()
                    curwgt.view().back()
            elif buttonReply == QMessageBox.No:
                print('Save clicked.')
            




        else:
            buttonReply3 = QMessageBox.warning(
                self,"주의","이 페이지는 악성 글 탐지를 지원하지 않습니다",QMessageBox.Yes | QMessageBox.No
            )
            

    def navOpen(self):
        f=open('./preds/prediction.csv','r')
        l=[]
        lo=[0,0,0,0]
        rdr = csv.reader(f)
        for line in rdr:
            l.append(line)
        f.close()
        for p in range(0,len(l)):
            for j in range(len(l[p])):
                if l[p][j]=="gender":
                    lo[0]+=1
                elif l[p][j]=="hate":
                    lo[1]+=1
                elif l[p][j]=="offensive":
                    lo[2]+=1
                elif l[p][j] == "other":
                    lo[3]+=1
        print(lo)

        
    def refreshNavBarState(self):
        curwgt = self._tabWidget.currentWidget()
        if isinstance(curwgt, WebPageWidget):
            history = curwgt.view().history()
            self._navBar.btnBackward.setEnabled(history.canGoBack())
            self._navBar.btnForward.setEnabled(history.canGoForward())

            bookmark_url_list = self._bookMarkManager.urlList()
            self._navBar.setBookMarkStatus(curwgt.view().url().toString() in bookmark_url_list)

    def addWebPageTab(self, url: Union[str, QUrl] = 'about:blank'):
        view = WebPageWidget(parent=self, url=url)
        self.setWebPageViewSignals(view)
        self.addTabCommon(view)

    def addWebPageView(self, view: Union[WebView, None]):
        if view is None:
            widget = WebPageWidget(parent=self)
        else:
            widget = WebPageWidget(parent=self, view=view)
        self.setWebPageViewSignals(widget)
        self.addTabCommon(widget)

    def addWebPageWidget(self, widget: WebPageWidget):
        self.setWebPageViewSignals(widget)
        self.addTabCommon(widget)

    def setWebPageViewSignals(self, view: WebPageWidget):
        view.sig_page_title.connect(partial(self.setWebPageTitle, view))
        view.sig_page_icon.connect(partial(self.setWebPageIcon, view))
        view.sig_new_tab.connect(self.addWebPageView)
        view.sig_new_window.connect(self.openNewWindow)
        view.sig_close.connect(partial(self.closeWebPageTab, view))
        view.sig_home.connect(partial(self.goHome, view))
        view.sig_page_url.connect(partial(self.setWebPageUrl, view))
        view.sig_edit_url_focus.connect(self._navBar.setEditUrlFocused)
        view.sig_load_started.connect(partial(self.onPageLoadStarted, view))
        view.sig_load_finished.connect(partial(self.onPageLoadFinished, view))
        view.sig_js_result.connect(self.onJavaScriptResult)

    def addTabCommon(self, widget: WebPageWidget):
        index = self._tabWidget.count() - 1
        title = widget.view().title()
        if len(title) == 0:
            title = 'Empty'
        self._tabWidget.insertTab(index, widget, title)
        # add close button in tab
        index = self._tabWidget.indexOf(widget)
        btn = QPushButton()
        btn.setIcon(QIcon('./Resource/close.png'))
        btn.setFlat(True)
        btn.setFixedSize(16, 16)
        btn.setIconSize(QSize(14, 14))
        btn.clicked.connect(partial(self.closeWebPageTab, widget))
        self._tabWidget.tabBar().setTabButton(index, QTabBar.RightSide, btn)
        self._tabWidget.setCurrentIndex(index)

    def closeWebPageTab(self, view: QWidget):
        if isinstance(view, WebPageWidget):
            index = self._tabWidget.indexOf(view)
            self._tabWidget.removeTab(index)
            view.release()

    def closeWebPageTabs(self, views: List[QWidget]):
        for view in views:
            self.closeWebPageTab(view)

    def closeWebPageAll(self):
        views = [self._tabWidget.widget(i) for i in range(self._tabWidget.count())]
        for view in views:
            idx = self._tabWidget.indexOf(view)
            if isinstance(view, WebPageWidget):
                self._tabWidget.removeTab(idx)
                view.release()

    def setWebPageTitle(self, view: WebPageWidget, title: str):
        index = self._tabWidget.indexOf(view)
        if title == 'about:blank':
            self._navBar.setEditUrlFocused()
        self._tabWidget.setTabText(index, title)
        self._tabWidget.setTabToolTip(index, title)

    def setWebPageIcon(self, view: WebPageWidget, icon: QIcon):
        index = self._tabWidget.indexOf(view)
        self._tabWidget.setTabIcon(index, icon)

    def setWebPageUrl(self, view: WebPageWidget, url: str):
        if self._tabWidget.currentWidget() == view:
            self._navBar.editUrl.setText(url)

    def onPageLoadStarted(self, view: WebPageWidget):
        curwgt = self._tabWidget.currentWidget()
        if curwgt == view:
            self._navBar.setIsLoading(True)
            self.refreshNavBarState()

    def onPageLoadFinished(self, view: WebPageWidget):
        curwgt = self._tabWidget.currentWidget()
        if curwgt == view:
            self._navBar.setIsLoading(False)
            self.refreshNavBarState()

    def closeEvent(self, a0: QCloseEvent) -> None:
        self.release()

    def openNewWindow(self, view: Union[WebView, None]):
        if view is None:
            newwnd = WebBrowserWindow(self)
        else:
            newwnd = WebBrowserWindow(self, init_url=None)
            newwnd.addWebPageView(view)
        newwnd.show()
        newwnd.resize(self.size())

    def keyPressEvent(self, a0: QKeyEvent) -> None:
        modifier = QApplication.keyboardModifiers()
        if a0.key() == Qt.Key_N:
            if modifier == Qt.ControlModifier:
                self.openNewWindow(None)
        elif a0.key() == Qt.Key_T:
            if modifier == Qt.ControlModifier:
                self.addWebPageTab()
        elif a0.key() == Qt.Key_W:
            if modifier == Qt.ControlModifier:
                curwgt = self._tabWidget.currentWidget()
                self.closeWebPageTab(curwgt)
        elif a0.key() == Qt.Key_H:
            if modifier == Qt.ControlModifier:
                curwgt = self._tabWidget.currentWidget()
                if isinstance(curwgt, WebPageWidget):
                    self.goHome(curwgt)
                else:
                    pass
        elif a0.key() == Qt.Key_F6:
            self._navBar.setEditUrlFocused()

    def onTabWidgetCurrentChanged(self):
        if self._tabWidget.currentIndex() == self._tabWidget.count() - 1:
            if self._tabWidget.count() > 1:
                self._tabWidget.setCurrentIndex(self._tabWidget.count() - 2)
        curwgt = self._tabWidget.currentWidget()
        if isinstance(curwgt, WebPageWidget):
            self._navBar.editUrl.setText(curwgt.url().toString())
        else:
            self._navBar.editUrl.clear()

    def onTabNewWindow(self, index: int):
        widget = self._tabWidget.widget(index)
        self._tabWidget.removeTab(index)
        newwnd = WebBrowserWindow(self, init_url=None)
        if isinstance(widget, WebPageWidget):
            newwnd.addWebPageWidget(widget)
        newwnd.show()
        newwnd.resize(self.size())

    def onTabCloseView(self, index: int):
        view = self._tabWidget.widget(index)
        self.closeWebPageTab(view)

    def onTabCloseViewOthers(self, index: int):
        view = self._tabWidget.widget(index)
        lst = []
        for i in range(self._tabWidget.count()):
            wgt = self._tabWidget.widget(i)
            if wgt != view:
                lst.append(wgt)
        self.closeWebPageTabs(lst)

    def onTabCloseRight(self, index: int):
        lst = []
        for i in range(index + 1, self._tabWidget.count()):
            wgt = self._tabWidget.widget(i)
            lst.append(wgt)
        self.closeWebPageTabs(lst)

    def goHome(self, view: WebPageWidget):
        view.load(self._config.url_home)

    def toggleNavigationBar(self):
        if self._navBar.isVisible():
            self._navBar.hide()
        else:
            self._navBar.show()

    def toggleBookMarkBar(self):
        if self._bookmarkBar.isVisible():
            self._bookmarkBar.hide()
        else:
            self._bookmarkBar.show()

    def toggleDevTool(self):
        if self._devWidget.isVisible():
            self._devWidget.hide()
        else:
            self._devWidget.show()

    def showAboutPage(self):
        curwgt = self._tabWidget.currentWidget()
        if isinstance(curwgt, WebPageWidget):
            page = curwgt.view().page()
            msg = f'URL: {page.url().toString()}'
            msg += f'\nTitle: {page.title()}'
            msg += f'\nIcon URL: {page.iconUrl().toString()}'
            print(msg)
            QMessageBox.information(self, 'Page Info', msg)

    def resizeEvent(self, a0: QResizeEvent) -> None:
        w, h = self.size().width(), self.size().height()
        self._splitter.resize(w, h)

    def runJavaScript(self, script: str):
        curwgt = self._tabWidget.currentWidget()
        if isinstance(curwgt, WebPageWidget):
            curwgt.runJavaScript(script)

    def onJavaScriptResult(self, obj: object):
        self._devWidget.setJsResult(obj)
    

if __name__ == '__main__':
    import sys
    from PyQt5.QtCore import QCoreApplication

    QApplication.setStyle('fusion')
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    wnd_ = WebBrowserWindow()
    wnd_.show()
    wnd_.resize(600, 600)

    app.exec_()