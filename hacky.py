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
    print('\tPress 1 to enroll user')
    print('\tPress 2 to edit user data')
    print('\tPress 3 to delete user')
    print('\tPress 4 to view user list')
    print('\tPress 5 to exit')

    choice = input('> ')
    return choice

def enroll_print(idx=None):
    idx = finger.enroll(idx)
    print('Remove finger.')
    while finger.is_finger_pressed():
        print('.', end='')
        time.sleep(1)
    print()
    return idx
    
    
if __name__ == '__main__':
    app = clouddb.create_app()
    app.app_context().push()

    while True:
        print()
        res = options()
        if res == '1':
            accno = input('Enter account number: ')
            phoneNum = input('Enter phone number: ')
            fingerID = enroll_print()

            if not accno or not phoneNum or fingerID is None:
                print('Enroll failed!')
                continue
            
            record_dict = {'accountNum': accno, 'fingerID': fingerID, 'phoneNum': phoneNum}
            clouddb.create(record_dict)
            print('Enroll complete.')
            
        elif res == '2':
            accno = input('Enter account number: ')
            record = clouddb.read(accno)
            if not record:
                print('Record does not exist!')
                continue
            
            fingerID = record['fingerID']
            if input('Update fingerprint? Y/N? ').lower().startswith('y'):
                finger.delete(fingerID)     # delete old print
                fingerID = enroll_print(fingerID) # enroll new one
                
            phoneNum = record['phoneNum']
            if input('Update phone number? Y/N? ').lower().startswith('y'):
                phoneNum = input('Enter phone number: ')

            if fingerID is None or not phoneNum:
                print('Update failed!')
            else:
                record['fingerID'] = fingerID
                record['phoneNum'] = phoneNum
                clouddb.update(record, accno)
                print('Update complete.')
                
        elif res == '3':
            accno = input('Enter account number: ')
            record = clouddb.read(accno)
            if not record:
                print('Record does not exist!')
                continue
            
            fingerID = record['fingerID']
            finger.delete(fingerID)
            clouddb.delete(accno)
            print('Delete complete.')

        elif res == '4':
            print('A/C NUMBER\tPHONE NUMBER\tFINGER ID')
            offset = None
            while True:
                ret = clouddb.list(cursor=offset)
                records = ret[0]
                offset = ret[1]
                for record in records:
                    print('{}\t{}\t{}'.format(str(record['accountNum']).zfill(8), record['phoneNum'], record['fingerID']))
                if not offset:
                    break               
            
        elif res == '5':
            print('Exiting.')
            break
