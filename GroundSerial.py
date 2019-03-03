import asyncio
import aioconsole
#import keyboard
import aioserial

IDLENGTH=1
DATALENGTH=4
BAUDRATE=921600
#BAUDRATE=9600

IdSet = None

COM_ID = {
    "arm": 'r',
    "cameras on": 'C',
    "cameras off": 'O',
    "halo": 'H',
    "satcom": 's',
    "reset": 'R',
    "ping": 'p',
    "main": 'm',
    "drogue": 'd'
}

# Good response -> Gxxxx
# Bad response -> BBBBB
Good_ID = 'G'.encode('ascii')
Bad_ID = 'B'.encode('ascii')

COM_NAME = {}
for x in COM_ID:
    COM_NAME[COM_ID[x]] = x

handle_data = None


async def _read_data():
    global aioserial_com
    chunkLength = IDLENGTH + DATALENGTH
    byteList = []
    while True:
        newbyte = await aioserial_com.read_async(1)
        byteList.append(newbyte)
        #print("Byte buffer: " + str(len(byteList)))

        while len(byteList)>= chunkLength:
            if byteList[0] == Good_ID and byteList[IDLENGTH].decode("ascii") in COM_NAME.keys() and _are_all(byteList[IDLENGTH:DATALENGTH], byteList[IDLENGTH]):
                print("Successful " + COM_NAME[byteList[IDLENGTH].decode("ascii")])
                del byteList[0:chunkLength]

            elif _are_all(byteList[0:chunkLength], Bad_ID):
                print("Failure!")
                del byteList[0:chunkLength]

            elif len(byteList) > chunkLength and byteList[0] in IdSet and byteList[chunkLength] in IdSet:
                chunk = byteList[0:chunkLength]
                intChunk = list(map(_byte_to_int, chunk))
                handle_data(intChunk)
                del byteList[0:chunkLength]
                #if intChunk[0] == 116:
                #   print("t " + str(intChunk))

            elif len(byteList) > chunkLength:
                del byteList[0]

            else:
                break


def _byte_to_int(byte):
    return int.from_bytes(byte, byteorder='little', signed=False)


def _are_all(list, expected):
    for x in list:
        if x != expected:
            return False
    return True


async def _read_input():
    global aioserial_com
    global COM_ID

    while True:
        word = await aioconsole.ainput()
        if word in COM_ID:
            bytes = COM_ID[word].encode('ascii') * (IDLENGTH + DATALENGTH)
            await aioserial_com.write_async(bytes)
            print("Sent!")

        elif word == "quit":
            print("Bye!")
            exit()

        else:
            bytes = word.encode('ascii')
            await aioserial_com.write_async(bytes)
            print("Sent!")


def on_triggered():
    global aioserial_com
    asyncio.run(aioserial_com.write_async(b"add"))
    print("Triggered!")


async def _run():
    if handle_data is None or IdSet is None:
        print("Bad init")
        return

    task1 = asyncio.create_task(
        _read_data())

    task2 = asyncio.create_task(
        _read_input())

    print("Starting Serial")

    await task1
    await task2


def init(handler, dataIdSet):
    global handle_data
    global IdSet
    handle_data = handler
    IdSet = dataIdSet

    IdSet.add(Good_ID)
    IdSet.add(Bad_ID)

    asyncio.run(_run())

com = None
while not com:
    var = input("Please enter a COM #: ")
    try:
        com = int(var)
    except:
        print("bad int")

print("Set to COM"+str(com))
aioserial_com = aioserial.AioSerial(port="COM"+str(com), baudrate=BAUDRATE)

#print('Press and release your desired shortcut: ')
#shortcut = keyboard.read_hotkey()
#print('Shortcut selected:', shortcut)
#keyboard.add_hotkey(shortcut, on_triggered)
