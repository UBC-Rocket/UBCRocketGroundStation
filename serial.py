import asyncio
import aioconsole
import keyboard
import aioserial
import sys

BYTEORDER='little'
IDLENGTH=1
DATALENGTH=4
IdSet = {b"t", b"A"}


def _handle_data(data):
    print(data)


async def _read_data():
    global aioserial_com
    chunkLength = IDLENGTH + DATALENGTH
    byteList = []
    while True:
        newbyte = await aioserial_com.read_async(1)
        byteList.append(newbyte)

        while len(byteList)>(chunkLength):
            if byteList[0] in IdSet and byteList[chunkLength] in IdSet:
                chunk = byteList[0:(chunkLength)]
                intChunk = list(map(_byte_to_int, chunk))
                _handle_data(intChunk)
                del byteList[0:(chunkLength)]
            else:
                del byteList[0]



def _byte_to_int(byte):
    return int.from_bytes(byte, byteorder=BYTEORDER, signed=False)


async def _read_input():
    while True:
        word = await aioconsole.ainput()
        print(word)


def on_triggered():
    global aioserial_com
    asyncio.run(aioserial_com.write_async(b"add"))
    print("Triggered!")


async def main():
    task1 = asyncio.create_task(
        _read_data())

    task2 = asyncio.create_task(
        _read_input())

    await task1
    await task2


com = None

while not com:
    var = input("Please enter a COM #: ")
    print("You entered " + str(var))
    try:
        com = int(var)
    except:
        print("bad int")

print("good int")
aioserial_com = aioserial.AioSerial(port="COM"+str(com))

print('Press and release your desired shortcut: ')
shortcut = keyboard.read_hotkey()
print('Shortcut selected:', shortcut)
keyboard.add_hotkey(shortcut, on_triggered)

print("starting")
asyncio.run(main())
