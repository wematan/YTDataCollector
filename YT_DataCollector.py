import signal
import time
import youtube_dl
import os
import argparse
import threading
try:
    import ConfigParser
    from livestreamer import Livestreamer
    from livestreamer.exceptions import LivestreamerError
except:
    print "Your missing dependencies Please run depends_tool.py from SVN repo under Tools."
    exit(1)


NAME_FORMAT = format("{output_location}\{name}_{time}.mp4")
COMMAND_FORMAT = format("D:\work\Livestreamer\livestreamer.exe -a="" -p=\"ffmpeg -i - {0}\" -v {1} best")


class recordingThread (threading.Thread):
    def __init__(self, threadID, output_location, name, yt_stream, start_time):
        threading.Thread.__init__(self)

        self.threadID = threadID
        self.output = os.path.abspath(output_location)
        self.name = name
        self.start_time = start_time
        self.bufferSize = 1024
        self.maxSize = self.bufferSize*1024*50 # 10 MB videos
        self.livestreamer = Livestreamer()
        self.numOfIndexes = 5

        self.yt_stream = yt_stream.strip('\'"')

    def run(self):
        print "Starting %s Thread Recorder - %s" % (self.name, self.start_time)
        name_conv_dict = {'output_location': self.output,
                           'name': self.name,
                           'time': time.strftime("%H%M_%d%b%y")}
        output_location = NAME_FORMAT.format(**name_conv_dict)


        try:
            available_streams = self.livestreamer.streams(self.yt_stream)
            bestStream = available_streams['best']
            stream_obj = bestStream.open()
            for i in range(self.numOfIndexes):
                outVid = open(output_location.replace(".mp4", "_"+str(i)+".mp4"), 'ab')
                currByteCount = 0
                while currByteCount < self.maxSize:
                    data = stream_obj.read(512*1024)
                    outVid.write(data)
                    currByteCount += 512*1024
                    outVid.flush()

            stream_obj.close()


        except LivestreamerError as err:
            print self.threadID + " Exception."
            print err

        except Exception, e:
            print self.threadID + " Exception."
            print e.message

        print self.name + " Done Recording."
        outVid.close()

        print self.name + " Re-encoding..."
        self.reencode()
        print self.name + " Re-encoding Done."

if __name__ == "__main__":
    argparser = argparse.ArgumentParser(description='Data Collection Tool.')
    argparser.add_argument('-c', type=str, required=True, help='Config File')
    argparser.add_argument('-o', type=str, required=True, help='Output Location')
    args = argparser.parse_args()

    output_location = args.o

    if not os.path.exists(output_location):
        os.mkdir(output_location)

    config = ConfigParser.ConfigParser()
    config.readfp(open(args.c))

    #logger = logging()
    servers = config.items(section="streams")
    timeout = config.items(section="timeout")
    threadPoll = [None] * len(servers)
    for server in servers:
        id = servers.index(server)
        name, stream = server
        threadPoll[id] = recordingThread(id, output_location, name, stream, time.strftime("%H:%M %d%b%y"))

    for thread in threadPoll:
        thread.start()

    for thread in threadPoll:
        thread.join()


