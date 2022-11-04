from urllib import parse
from ast import literal_eval
import requests
from datetime import date, timedelta
import time
import RPi.GPIO as GPIO
from threading import Thread

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

today = date.today()
yesterday = date.today() - timedelta(1)
code = "005930"
icode = list(map(int ,list(code)))
price_today = 0
price_yesterday = 0
clock_mode = -1
set_code = False
code_stage = 0
disp_set_code = True
t = 0

digits = (0,1,2,3,4,5,6,7)
segments =  (8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23)

for digit in digits:
    GPIO.setup(digit, GPIO.OUT)
    GPIO.output(digit, 1)

for segment in segments:
    GPIO.setup(segment, GPIO.OUT)
    GPIO.output(segment, 0)

GPIO.setup(24, GPIO.IN)
GPIO.setup(25, GPIO.IN)

num = {' ':(0,0,0,0,0,0,0),
    '0':(1,1,1,1,1,1,0),
    '1':(0,1,1,0,0,0,0),
    '2':(1,1,0,1,1,0,1),
    '3':(1,1,1,1,0,0,1),
    '4':(0,1,1,0,0,1,1),
    '5':(1,0,1,1,0,1,1),
    '6':(1,0,1,1,1,1,1),
    '7':(1,1,1,0,0,0,0),
    '8':(1,1,1,1,1,1,1),
    '9':(1,1,1,1,0,1,1),
    'up':(1,1,0,0,0,1,1),
    'down':(0,0,0,0,0,0,1),
    '-':(0,0,1,1,1,0,1),
    's':(1,0,1,1,0,1,1,),
    'e':(1,0,0,1,1,1,1),
    't':(0,0,0,1,1,1,1),
    ' ':(0,0,0,0,0,0,0),
    'c':(0,0,0,1,1,0,1),
    'o':(0,0,1,1,1,0,1),
    'd':(0,1,1,1,1,0,1),
    'e':(1,0,0,1,1,1,1)}

def sw1_inturrupt(var):
    global code_stage, icode, code

    if set_code == True:
        if code_stage == 0:
            icode[0] += 1
            if icode[0] == 10:
                icode[0] = 0
        elif code_stage == 1:
            icode[1] += 1
            if icode[1] == 10:
                icode[1] = 0
        elif code_stage == 2:
            icode[2] += 1
            if icode[2] == 10:
                icode[2] = 0
        elif code_stage == 3:
            icode[3] += 1
            if icode[3] == 10:
                icode[3] = 0
        elif code_stage == 4:
            icode[4] += 1
            if icode[4] == 10:
                icode[4] = 0
        elif code_stage == 5:
            icode[5] += 1
            if icode[5] == 10:
                icode[5] = 0

    code = conv_code(0, icode)

def sw2_inturrupt(var):
    global set_code, code_stage, disp_set_code, code, price_today, price_yesterday

    icode = conv_code(1, code)

    if set_code == True:
        if code_stage == 5:
            set_code = False
            disp_set_code = True
            code_stage = 0
            code = conv_code(0, icode)
            price_today = check_data(code, today)
            price_yesterday = check_data(code, yesterday)
            print(price_today)
            return

        code_stage += 1
    else:
        set_code = True
        disp_set_code = True
        code_stage = 0

def conv_code(i, var):
    if i == 1:
        intlcode = list(map(int ,list(var)))
        return intlcode
    elif i == 0:
        strcode = ''.join(map(str, var))
        return strcode

def get_prise(code, start_time) :
    get_param = {
        'symbol' : code,
        'requestType' : 1,
        'startTime' : start_time,
        'endTime' : start_time,
        'timeframe' : 'day'
    }

    get_param = parse.urlencode(get_param)
    url = "https://api.finance.naver.com/siseJson.naver?%s"%(get_param)
    response = requests.get(url)
    return literal_eval(response.text.strip())

def check_data(code, day) :
    days = day.strftime('%Y%m%d')
    for loop in range(1, 11) :
        data = get_prise(code, days)
        if len(data) == 1 :
            days_tmp = day - timedelta(loop)
            days = int(days_tmp.strftime('%Y%m%d'))
        else :
            return data[1][4]

def seg_thread(val) :
    global set_code, disp_set_code

    while True:
        if set_code == True and disp_set_code == True:
            c = "edoctes "
            for l in range(0, 100):
                for digit in range(0, 8):
                    for loop in range(0, 7):
                        if digit < 4:
                            GPIO.output(segments[loop + 8], num[c[digit]][loop])
                        else:
                            GPIO.output(segments[loop], num[c[digit]][loop])

                    GPIO.output(digits[7 - digit], 0)
                    time.sleep(0.001)
                    GPIO.output(digits[7 - digit], 1)
                    time.sleep(0.001)
            disp_set_code = False

        elif set_code == True and disp_set_code == False:
            s = code[::-1]

            for digit in range(0, 6):
                for loop in range(0, 7):
                    if digit < 4:
                        GPIO.output(segments[loop + 8], num[s[digit]][loop])
                        if (int(time.ctime()[18:19]) % 2 == 0) and (digit == 5 - code_stage):
                            GPIO.output(23, 1)
                        else:
                            GPIO.output(23, 0)
                    else:
                        GPIO.output(segments[loop], num[s[digit]][loop])
                        if (int(time.ctime()[18:19]) % 2 == 0) and (digit == 5 - code_stage):
                            GPIO.output(15, 1)
                        else:
                            GPIO.output(15, 0)

                GPIO.output(digits[7 - digit], 0)
                time.sleep(0.001)
                GPIO.output(digits[7 - digit], 1)
                time.sleep(0.001)
                GPIO.output(15, 0)

        elif set_code == False and clock_mode == -1:
            d = time.strftime('%m%d%H%M')[::-1]

            for digit in range(0, 8):
                for loop in range(0, 7):
                    if digit < 4:
                        GPIO.output(segments[loop + 8], num[d[digit]][loop])
                        if (int(time.ctime()[18:19]) % 2 == 0) and (digit == 2):
                            GPIO.output(23, 1)
                        else:
                            GPIO.output(23, 0)
                    else:
                        GPIO.output(segments[loop], num[d[digit]][loop])

                GPIO.output(digits[7 - digit], 0)
                time.sleep(0.001)
                GPIO.output(digits[7 - digit], 1)
                time.sleep(0.001)
        else:
            s = str(price_today)[::-1]

            for digit in range(0, len(s)):
                for loop in range(0, 7):
                    if digit < 4:
                        GPIO.output(segments[loop + 8], num[s[digit]][loop])
                    else:
                        GPIO.output(segments[loop], num[s[digit]][loop])

                GPIO.output(digits[7 - digit], 0)
                time.sleep(0.001)
                GPIO.output(digits[7 - digit], 1)
                time.sleep(0.001)

            if price_today > price_yesterday:
                for loop in range(0, 7):
                    GPIO.output(segments[loop], num['up'][loop])
            elif price_today < price_yesterday:
                for loop in range(0, 7):
                    GPIO.output(segments[loop], num['-'][loop])
            else:
                for loop in range(0, 7):
                    GPIO.output(segments[loop], num['down'][loop])

            GPIO.output(digits[0], 0)
            time.sleep(0.001)
            GPIO.output(digits[0], 1)
            time.sleep(0.001)

def time_thread(var) :
    global clock_mode, price_today

    t = 0

    while True:
        if t == 12:
            print('Price update!, Segment change!')
            price_today = check_data(code, today)
            clock_mode = ~clock_mode
            time.sleep(15)
            t = 0
        elif t == 0:
            time.sleep(15)
            t += 1
        elif t % 4 == 0:
            print('Price update!')
            price_today = check_data(code, today)
            time.sleep(15)
            t += 1
        elif t % 3 == 0:
            print('Segment change!')
            clock_mode = ~clock_mode
            time.sleep(15)
            t += 1
        else:
            time.sleep(15)
            t += 1


    
#====main====

t1 = Thread(target = seg_thread, args = (1,))
t2 = Thread(target = time_thread, args = (1,))

t1.start()
t2.start()

GPIO.add_event_detect(24, GPIO.FALLING, callback = sw1_inturrupt, bouncetime = 250)
GPIO.add_event_detect(25, GPIO.FALLING, callback = sw2_inturrupt, bouncetime = 250)

price_today = check_data(code, today)
price_yesterday = check_data(code, yesterday)

print(code, icode)
print(price_today, price_yesterday)

while True:
    print("working.")
    time.sleep(5)
    print("working..")
    time.sleep(5)
    print("working..")
    time.sleep(5)

t1.join()
t2.join()

GPIO.cleanup()
