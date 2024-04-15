def front_right(pos):
    newpos = {
        'x': pos['x'] + 0.5,
        'y': pos['y'] + 0.5,
        'z': pos['z']
    }
    return newpos

def front_left(pos):
    newpos = {
        'x': pos['x'] - 0.5,
        'y': pos['y'] + 0.5,
        'z': pos['z']
    }
    return newpos

def back_right(pos):
    newpos = {
        'x': pos['x'] + 0.5,
        'y': pos['y'] - 0.5,
        'z': pos['z']
    }
    return newpos

def back_left(pos):
    newpos = {
        'x': pos['x'] - 0.5,
        'y': pos['y'] - 0.5,
        'z': pos['z']
    }
    return newpos