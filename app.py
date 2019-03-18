from configparser import ConfigParser

import storage
import server
from processor import Processor


if __name__ == "__main__":
    config = ConfigParser()
    config.read("conf.ini")
    host = config.get("SERVER", "host")
    port = config.getint("SERVER", "port")
    storage_name = config.get("STORAGE", "name")
    process_period = config.getint("PROCESSOR", "period")

    # Initializing storage
    storage.init(storage_name)
    processor = Processor(process_period, storage_name)

    try:
        processor.start()  # Start file processor
        server.app.run(port=port)  # Start web application
    except Exception as e:
        print(e)
        storage.close()
        processor.join()
        processor.terminate()
