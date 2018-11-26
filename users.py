import requests
import nexmo
import pprint

from authorizenet import apicontractsv1
from authorizenet.apicontrollers import*
from decimal import*

import clouddb
import sys
import time
from fps import Fingerprint

port = 'COM7'           #Windows
#port = '/dev/ttyUSB0'   #Linux


finger = Fingerprint(port, 9600)
if finger.init() and finger.open():
    print('Fingerprint sensor detected.')
else:
    print('Sensor not found! Exiting.')
    sys.exit(0)
    
def options():
    print('Options: ')
    print('\tPress 1 to view transactions')
    print('\tPress 2 to make a payment')
    print('\tPress 3 to exit')

    choice = input('> ')
    return choice

headers = {
    'Version': '1.0',
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}



client = nexmo.Client(key='ec402a11', secret='TFDfiJfTgn3uRsVZ')



# UI - either CLI or GUI:
#       New user - Account Number, Fingerprint... rest of data on Capital One database (retrieve and show everything) ... can you confirm? Then collect fingerprint.collect
#       View my transactions - Don't retrieve data until verified by fingerprint for security reasons.security

#Two databases for extra safety. One for fingerprints. The other will store all the sensitive user data. TLS.



# account number to test with 00030740
# getTransactionData ('00030740', 0)

def getTransactionData (accountNum) :
    "This retrieves Transaction Data for given account number from Capital One Database"

    transactions = requests.get('https://sandbox.capitalone.co.uk/open-banking-example/accounts/00030740/transactions',
                     headers=headers, verify=False).json()

    result = []
    for t in transactions:
        result.append({
                        "currency" : t['amount']['currency'],
                        "price" : t['amount']['amount'],
                        "merchant" : t['merchantDetails']['merchantName'],
                        "time" : t['bookingDateTime']
                        })

    return result



#makePayment ("4111111111111111", "2020-12", '2962')

def makePayment (cardNumber, expirationDate, amount):
    merchantAuth = apicontractsv1.merchantAuthenticationType()
    merchantAuth.name = '9NYu8k3W'
    merchantAuth.transactionKey = '8Ah6c44U5skFE5BG'

    creditCard = apicontractsv1.creditCardType()
    #creditCard.cardNumber = "4111111111111111"
    #creditCard.expirationDate = "2020-12"
    creditCard.cardNumber = cardNumber
    creditCard.expirationDate = expirationDate


    payment = apicontractsv1.paymentType()
    payment.creditCard = creditCard

    transactionrequest = apicontractsv1.transactionRequestType()
    transactionrequest.transactionType = "authCaptureTransaction"
    transactionrequest.amount = Decimal(amount)
    transactionrequest.payment = payment


    createtransactionrequest = apicontractsv1.createTransactionRequest()
    createtransactionrequest.merchantAuthentication = merchantAuth
    createtransactionrequest.refId = "MerchantID-0001"

    createtransactionrequest.transactionRequest = transactionrequest
    createtransactioncontroller = createTransactionController(
        createtransactionrequest)
    createtransactioncontroller.execute()

    response = createtransactioncontroller.getresponse()

    if (response.messages.resultCode == "Ok"):
        #print("Transaction ID : %s" % response.transactionResponse.transId)
        return True
    #print("response code: %s" % response.messages.resultCode)
    return False



def sendSMS(src, phoneNum, msg):
    client.send_message({
        'from': src,
        'to': phoneNum,
        'text': msg
    })




currencyLUT = {'GBP': "£", 'USD': "$", 'EUR': "€"}


if __name__ == '__main__':
    app = clouddb.create_app()
    app.app_context().push()

    while True:
        print()
        res = options()
        if res == '1':
            accno = input('Enter account number: ')
            if not accno:
                continue
            record = clouddb.read(str(int(accno)))
            if not record:
                print('Account not found!')
                continue
            
            print('Place finger.')
            while not finger.capture_finger():
                print('.', end='')
                time.sleep(1)
                
            if not finger.verify(record['fingerID']):
                print('Access denied!')
                continue
                
            print('Welcome.')
            message = "Hi, you just viewed your CapitalOne transaction history. If this wasn't you then please contact CapitalOne."
            sendSMS ('NEXMO', record['phoneNum'], message)
            
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(getTransactionData(accno))
        
        elif res == '2':
            accno = input('Enter account number: ')
            record = clouddb.read(accno)
            if not record:
                print('Account not found!')
                continue
            
            print('Place finger.')
            while not finger.capture_finger():
                print('.', end='')
                time.sleep(1)
                
            if not finger.verify(record['fingerID']):
                print('Access denied!')
                continue
            
            cardno = input('Enter card number: ')
            expiry = input('Enter expiry date: ')
            amt = input('Enter amount: ')

            if makePayment(cardno, expiry, amt):
                print('Payment complete.')
                message = "Hi, a payment of %s GBP has just been made from your account. If this wasn't you, then please contact your bank." % (amt)
                sendSMS('NEXMO', record['phoneNum'], message)
                continue
            
            print('Payment failed!')
            
        elif res == '3':
            print('Exiting.')
            break
