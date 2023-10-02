with open('send.txt', 'w') as file:
    for i in range(1000):
        file.write(str(i*1111111) + "\n")