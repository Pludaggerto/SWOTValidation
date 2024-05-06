from DataArranger import DataArranger
from Joiner import Joiner
import logging

def main():

    log = logging.getLogger()
    handler = logging.StreamHandler()
    log.addHandler(handler)
    log.setLevel(logging.INFO)

    dataArranger = DataArranger()
    dataArranger.get_all_type_data()

    joiner = Joiner()
    joiner.select()

if __name__ == '__main__':
    main()