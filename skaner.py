#!/usr/bin/env python
# -*- coding: utf-8 -*-
import time
import serial
import struct

STX0 = 0x00                                         #Bity odpowiedzialne za komunikacje
STX1 = 0x55
STX2 = 0xAA
STX3 = 0x01
STX4 = 0x00

CMD_OPEN = 0x01                                     #Bity odpowiedzialne za uruchamiaie różnych funkcji na czytniku
CMD_CLOSE = 0x02                                    #(szczegóły w GT-511C1R_datasheet_V1 5_20140312)
CMD_LED = 0x12
CMD_GET_ENROLL_COUNT = 0x20
CMD_ENROLL_START = 0x22
CMD_ENROLL_1 = 0x23
CMD_ENROLL_2 = 0x24
CMD_ENROLL_3 = 0x25
CMD_IS_FINGER_PRESSED = 0x26
CMD_DELETE_ALL = 0x41
CMD_IDENTIFY = 0x51
CMD_CAPTURE_FINGER = 0x60

ACK = 0x30
NACK = 0x31

port = None


def delay(seconds):                                 #Funkcja służąca do odczekania zadanej ilości sekund
    time.sleep(seconds)

def GetHighByte(w):                                 #Funkcja zwracjąca starszą część bajtu
    return (w>>8)&0x00FF

def GetLowByte(w):                                  #Funkcja zwracjąca młodszą część bajtu 
    return w&0x00FF

def calcChecksum(package):                          #Funkcja odpowiedzialna za liczenie sumy kontrolnej
    checksum = 0
    for byte in package:
        checksum += ord(chr(byte))
    return int(checksum)

def waitForAnswer():                                #Funkcja oczekiwania na odpowiedź czytnika
    recv = bytearray(port.read(port.inWaiting()))
    emptyBytearray = bytearray()
    while True:    
        if recv == emptyBytearray:
            recv = bytearray(port.read(port.inWaiting()))
            delay(0.001)
            continue
        else:
            if len(recv) == 12:
                break
            else:
                print("received: " + str(recv))     #TODO check 
                print("len not 12 but continue..")
                continue
    return recv

def sendCmd(cmd, param=0):                          #Funkcja służąca do tworzenia "paczki" danych, oraz przesłania jej do czytnika i odebrania odpowiedzi.
    packetbytes = bytearray(12)
    packetbytes[0] = 0x55                           #Komenda startu 1
    packetbytes[1] = 0xAA                           #Komenda startu 2
    packetbytes[2] = 0x01                           #ID urządzenia-część 1         
    packetbytes[3] = 0x00                           #ID urządzenia-część 2   
    packetbytes[4] = (param & 0x000000ff)           #Parametr typu int po przeprowadzeniu konwersji do bitu - część 1
    packetbytes[5] = (param & 0x0000ff00) >> 8      #Parametr typu int po przeprowadzeniu konwersji do bitu - część 2
    packetbytes[6] = (param & 0x00ff0000) >> 16     #Parametr typu int po przeprowadzeniu konwersji do bitu - część 3
    packetbytes[7] = (param & 0xff000000) >> 24     #Parametr typu int po przeprowadzeniu konwersji do bitu - część 4
    packetbytes[8] = GetLowByte(cmd)                #Młodsze bity bajtu funkji wywoływanej w czytniku
    packetbytes[9] = GetHighByte(cmd)               #Starsze bity bajtu funkji wywoływanej w czytniku
    chksum = calcChecksum(packetbytes[0:9])
    packetbytes[10] = GetLowByte(chksum)            #Młodsze bity sumy kontrolnej
    packetbytes[11] = GetHighByte(chksum)           #Starsze bity sumy kontrolnej
    

    
    sent = port.write(bytes(packetbytes))
    if(sent != len(packetbytes)):
        print ("Error communicating")
        return -1

    recv = waitForAnswer()
    recvPkg = struct.unpack('cchihh', recv)
    if recvPkg[4] == NACK:
        print("error: %s" % recvPkg[3])
        return -2
    return recvPkg[3]


def startScanner():                                 #Funkcja rozpoczynająca komunikację
    print("Nawiązanie komunikacji ze skanerem\n")
    sendCmd(CMD_OPEN)


def stopScanner():                                  #Funkcja zakańczająca komunikację
    print("Rozwiązanie komunikacji ze skanerem\n")
    sendCmd(CMD_CLOSE)


def led(status=True):                               #Funkcja odpowiedzialna za włączanie i wyłączanie diody LED pod czytnikiem
    if status:
        sendCmd(CMD_LED, 1)
    else:
        sendCmd(CMD_LED, 0)


def enrollFail():                                   #Funkcja wskazująca błąd skanowania
    print("Błąd skanowania")
    led(False)
    stopScanner()


def identFail():                                    #Funkcja wskazująca błąd komunikacji
    print("Błąd identyfikacji")
    led(False)
    stopScanner()


def startEnroll(ident):                             #Funkcja rozpoczynająca skanowanie
    sendCmd(CMD_ENROLL_START, ident)


def waitForFinger(state):                           #Funkcja oczekująca na położenie palca
    if(state):
        while(sendCmd(CMD_IS_FINGER_PRESSED) == 0):
            time.sleep(0.1)
    else:
        while(sendCmd(CMD_IS_FINGER_PRESSED) > 0):
            time.sleep(0.1)

def captureFinger():
    return sendCmd(CMD_CAPTURE_FINGER)

def enroll(state):                                  #Funkcja wykorzystana w funkcji do dodawania rekordów; 
    if state == 1:                                  #zajmuje się przesyłania informacji o skanowaniu do czytnika
        return sendCmd(CMD_ENROLL_1)
    if state == 2:
        return sendCmd(CMD_ENROLL_2)
    if state == 3:
        return sendCmd(CMD_ENROLL_3)


def identifyUser():                                 #Funkcja wykorzystana w funkcji do sprawdzania obecności; zajmuje się identyfikacją odcisku
    delay(1)
    return sendCmd(CMD_IDENTIFY)

def getEnrollCount():                               #Funkcja pobierająca od czytnika wolną pozycje ID do zapisu
    return sendCmd(CMD_GET_ENROLL_COUNT)

def removeAll():
    return sendCmd(CMD_DELETE_ALL)                  #Funkcja do usuwania odcisków z pamięci czytnika

def DeleteBase(studentBase):                        #Funkcja do usuwania bazy
    startScanner()
    led()                                    
    studentBase = [0 for x in range(20)]
    removeAll()
    print(studentBase)
    print("Baza wyczyszczona pomyślnie\n")
    led(False)
    stopScanner()
    return studentBase
    

def AddToBase(studentBase):                                    #Funkcja odpowiedzialna za dodawanie rekordów do bazy(zamknięta w pętli)
    answear = 1
    startScanner()
    led()
    while answear == 1:
        newID = getEnrollCount()
        studentBase[newID]=input("Podaj numer indeksu: ")
        print("Skanowanie rozpoczęte\n") 
        startEnroll(newID)
        print("Połóż palec do zeskanowania\n")
        waitForFinger(False)
        if captureFinger() < 0:
            enrollFail()
            return
        enroll(1)
        print("Zdejmij palec\n")
        waitForFinger(True)
        print("Połóż palec ponownie\n")
        waitForFinger(False)
        if captureFinger() < 0:
            enrollFail()
            return
        enroll(2)
        print("Zdejmij palec\n")
        waitForFinger(True)
        print("Połóż palec ponownie\n")
        waitForFinger(False)
        if captureFinger() < 0:
            enrollFail()
            return
        if enroll(3) != 0:
            enrollFail()
            return
        print("Zdejmij palec")
        print("\nAby dodać następną osobę wpisz 1")
        print("Aby wrócić do menu wpisz 2\n")
        answear = int(input("Podaj swój wybór: "))

    led(False)
    stopScanner()
    return studentBase
    

def CheckAbility(studentBase):                                 #Funkcja odpowiadająca za sprawdzanie obecności (zamknięta w pętli)
    import datetime
    listname = str(datetime.date.today()) + ".txt"
    answear = 1
    startScanner()
    led()
    while answear == 1:
        waitForFinger(True)
        print("Połóż palec na skanerze")
        waitForFinger(False)
        if captureFinger() < 0:
            identFail()
            return
        ident = identifyUser()
        if(ident >= 0 and ident < 21):
            print("Identity found: %d" % ident)
            file1 = open(listname, 'a')             #Zapis obecnych osób do pliku
            print(studentBase[ident])
            file1.write(str(studentBase[ident]))
            file1.write("     ")
            file1.write(str(datetime.datetime.now()))
            file1.write("\n")
        else:
            print("User not found")
        print("\nAby dalej sprawdzać obecność wpisz 1")
        print("Aby wrócić do menu wpisz 2\n")
        answear = int(input("Podaj swój wybór: "))

    led(False)
    stopScanner()
    return studentBase
    

def printMenu():                                    #Funkcja odpowiedzialna za wyświetlanie MENU
    print("\n************MENU************")
    print("1. Dodaj studenta do bazy")
    print("2. Sprawdź obecność")
    print("3. Wyczyść bazę")
    print("4. Zakończ")
    print("****************************\n")

def OpenBase(name, studentBase):
    file = open(name, "r")                          #Wczytanie bazy z pliku
    studentBase.clear()
    for line in file:
        studentBase.append(int(line))
    file.close()
    return studentBase
    

def SaveBase(name, studentBase):
    file = open(name, 'w')                          #Zapis bazy do pliku przed zamknięciem programu
    for element in studentBase:
        file.write(str(element) + "\n")
    file.close()
    print("Wyniki zostały zapisane w pliku")


def main():
    import os
    studentBase = []                                  #Tworzę bazę dadenstudentBase=

    for i in range(20):                                 #Uzupełniam ją 0
        studentBase.append(0)

    filename = "baza.txt"                           #Deklaracja nazwy pliku bazy   
    if filename in os.listdir():
        studentBase = OpenBase(filename, studentBase)

    user_choice = 0                                 #MENU programu, gdzie dokonuje się wyboru funkcji
    while user_choice != 4:
        printMenu()
        user_choice = int(input("Podaj swój wybór: "))

        if user_choice == 1:
            studentBase = AddToBase(studentBase)
        elif user_choice == 2:
            studentBase = CheckAbility(studentBase)
        elif user_choice == 3:
            studentBase = DeleteBase(studentBase)
        elif user_choice == 4:
            SaveBase(filename, studentBase)
        else:
            print("Brak opcji. Spróbuj ponownie.")


if __name__ == "__main__":                          #Ustawienia portu podłączenia czytnika
    try:
        if port is None:
            delay(0.1)
            port = serial.Serial('COM6',baudrate=9600,timeout=100)
        main()
    except Exception as e:
        print (e)
        port.close()
    finally:
        port.close()
