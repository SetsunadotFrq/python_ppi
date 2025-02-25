import time
import RPi.GPIO as GPIO
import datetime
import requests
import gspread
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

KEY_NAME = '/home/sangitan/ppi/rasppi-ppi-3c3df752b014.json' # Google認証キー
GOOGLE_FOLDER_ID = '1Xau9WcEP56djM0Yj1GqGq27sjwdWuUrp' # Google DriveのフォルダーID
GOOGLE_SHEET_ID = '1HcldzOvWkyIrmlSHUqPBFXK8XYDqy9o3A8khpPHuJRk' # Google SheetのID
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive'] # スプレッドシートとドライブに対するフルアクセス権限
credentials = service_account.Credentials.from_service_account_file(filename=KEY_NAME, scopes=scope) 
#LINE API Function
def _notify():
    url = "https://notify-api.line.me/api/notify"
    token = "svZnrwVVFKpKRNwwflVZsuRZelZ9ND1muY1OINcIm59"
    spreadurl = "https://docs.google.com/spreadsheets/d/1HcldzOvWkyIrmlSHUqPBFXK8XYDqy9o3A8khpPHuJRk/"
    headers = {'Authorization' : 'Bearer ' + token }
    message = "Security Alert:Please check.\n" + spreadurl
    payload = { "message" : message }
    r = requests.post( url , headers = headers , params = payload )
    print(r) #正しく接続できた場合は” 200”が表示されます。 
GPIO.setmode(GPIO.BCM)

#GPIO18pinを入力モードとし、pull up設定とします
GPIO.setup(18,GPIO.IN,pull_up_down=GPIO.PUD_UP)

#ドア開閉状態フラグ
flag = 1
oflg = 0
coflg = 0
ncflg = 0
o_time = ""

'''
memo
reedswitch

status = 0 ///Close
status = 1 ///Open
'''
#inf loop
while True:
    try:
        flag = GPIO.input(18)#GPIOピンからスイッチの状態を取得


        #ドアが開いたとき
        if flag == 1:
            print("Opened") ##Check message

            #初回目
            if o_time == "":
                o_time = datetime.datetime.now()
                tt = o_time.strftime('%Y/%m/%d %H:%M:%S')
                print(tt)
 

                #Google Spread Sheetに"ドアが開いたことを書き込み"
                gc = gspread.authorize(credentials) # Google Sheet認証
                wks = gc.open_by_key(GOOGLE_SHEET_ID).sheet1 # sheetをオープン
                records = wks.get_all_values() # 中身を取り出して配列に保存
                wks.update_cell(len(records) + 1,1,tt)
                wks.update_cell(len(records) + 1,2,"ドアが開きました")
                oflg = 1 
#初回目でないとき
            else:
                now_time = datetime.datetime.now() #今の時刻を取得
                str_ntime = now_time.strftime('%Y/%m/%d %H:%M:%S')

                comp = now_time - o_time #o_timeを減算

                one_min = datetime.timedelta(minutes = 1)
                thirty_min = datetime.timedelta(minutes = 2)#30 -> 2 test

                #Google Spread Sheetに"ドアが開いたままであることを書き込み"
                if comp >= one_min and comp <= thirty_min and coflg == 0:
                    gc = gspread.authorize(credentials) # Google Sheet認証
                    wks = gc.open_by_key(GOOGLE_SHEET_ID).sheet1 # sheetをオープン
                    records = wks.get_all_values() # 中身を取り出して配列に保存

                    wks.update_cell(len(records) + 1,1,str_ntime)
                    wks.update_cell(len(records) + 1,2,"ドアが開いて1分が経過しました")
                    _notify()
                    coflg = 1
#Google Spread Sheetに"ドアが閉じたことを書き込み"
                elif comp >= thirty_min and coflg == 1 and ncflg == 0:
                    gc = gspread.authorize(credentials) # Google Sheet認証
                    wks = gc.open_by_key(GOOGLE_SHEET_ID).sheet1 # sheetをオープン
                    records = wks.get_all_values() # 中身を取り出して配列に保存
                    wks.update_cell(len(records) + 1,1,str_ntime)
                    wks.update_cell(len(records) + 1,2,"ドアが開いて2分が経過しました　確認してください")
                    _notify()
                    ncflg = 1
#ドアが閉じたとき
        else:
            print("Close")
            if oflg == 1 or coflg == 1 or ncflg == 1:
                gc = gspread.authorize(credentials) # Google Sheet認証
                wks = gc.open_by_key(GOOGLE_SHEET_ID).sheet1 # sheetをオープン
                records = wks.get_all_values() # 中身を取り出して配列に保存
                wks.update_cell(len(records) + 1,1,str_ntime)
                wks.update_cell(len(records) + 1,2,"ドアが閉まりました")

                #o_time、フラグをリセット
                o_time = ""
                oflg,coflg,ncflg = 0

        #スリープ(1秒)
        time.sleep(1)

    except:
        break
