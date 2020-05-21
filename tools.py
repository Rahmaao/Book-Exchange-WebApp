def downloadHelper(data, filename):
    with open(filename, 'wb') as file:
        file.write(data)