import argparse
import piman


dispatchDict = {'server' : lambda args: piman.server(),
                'restart' : lambda args: piman.restart(args),
                'reinstall' : lambda args: piman.reinstall(args),
                'powercycle' : lambda args: piman.powercycle(args)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Raspberry Pi Manager')
    parser.add_argument('command', choices=dispatchDict)
    parser.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    function = dispatchDict[args.command]
    function(args.args)
