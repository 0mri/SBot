from bot.newegg import Newegg


def test():
    _attempt = 0
    while True:
        _attempt +=1
        (success, time)  = Newegg(test=True).start()
        with open('test.log', 'a') as f:
            f.write(f"attemppt: {_attempt}, {time} {'SUCCESS' if success else 'FAILED'}\n")