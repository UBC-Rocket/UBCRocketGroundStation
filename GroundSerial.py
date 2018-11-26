import asyncio
import aioconsole
#import keyboard
import aioserial

BYTEORDER='little'
IDLENGTH=1
DATALENGTH=4
BAUDRATE=921600

IdSet = None
handle_data = None


async def _read_data():
    global aioserial_com
    chunkLength = IDLENGTH + DATALENGTH
    byteList = []
    while True:
        newbyte = await aioserial_com.read_async(1)
        byteList.append(newbyte)

        while len(byteList)> chunkLength:
            if byteList[0] in IdSet and byteList[chunkLength] in IdSet:
                chunk = byteList[0:chunkLength]
                intChunk = list(map(_byte_to_int, chunk))
                handle_data(intChunk)
                del byteList[0:chunkLength]
            else:
                del byteList[0]



def _byte_to_int(byte):
    return int.from_bytes(byte, byteorder=BYTEORDER, signed=False)


async def _read_input():
    global aioserial_com
    while True:
        word = await aioconsole.ainput()
        if word == "add":
            await aioserial_com.write_async(b"add")
            print("Sent!")
        else:
            await aioserial_com.write_async(word.encode('ascii'))
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
