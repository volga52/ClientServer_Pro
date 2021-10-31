import subprocess

PROCESS = []

while True:
    ACTION = input('Выберите действие: q - выход, s - запустить сервер и клиенты, c - закрыть все окна: ')

    if ACTION == 'q':
        break

    elif ACTION == 's':
        # PROCESS.append(subprocess.Popen('python server.py -p 8888', creationflags=subprocess.CREATE_NEW_CONSOLE))
        PROCESS.append(subprocess.Popen('python client.py -n test1', creationflags=subprocess.CREATE_NEW_CONSOLE))
        PROCESS.append(subprocess.Popen('python client.py -n test2', creationflags=subprocess.CREATE_NEW_CONSOLE))
        PROCESS.append(subprocess.Popen('python client.py -n test3', creationflags=subprocess.CREATE_NEW_CONSOLE))

    elif ACTION == 'c':
        while PROCESS:
            VICTIM = PROCESS.pop()
            VICTIM.kill()
