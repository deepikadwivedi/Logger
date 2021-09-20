from flask import Flask,render_template, jsonify, request, abort
from flask_restful import Resource
import sys
import re

app = Flask(__name__)


class LogRequest():
    def __init__(self, request):
        self.filtered_request = False
        self.parse(request)
        self.result = []
        self.BLOCK_SIZE = 10

    def parse(self, request):
        if request.args.get('filename'):
            self.filename = request.args.get('filename')
        else:
            raise ValueError('Filename must be specified')
        self.query = request.args.get('query')
        if self.query:
            self.compiled_query = re.compile(self.query)
            self.filtered_request = True

        if request.args.get('numlines'):
            self.numlines = int(request.args.get('numlines'))
            if self.numlines < 1:
                raise ValueError('numlines must be a positive integer')
        else:
            self.numlines = 20
        self.file = open("/var/log/" + self.filename, "rb")

    def tail(self):
        lines_to_go = self.total_lines_remaining + 1
        blocks = [] # blocks of size BLOCK_SIZE, in reverse order starting                                                                
        hit_start = False
        # from the end of the file                                                                                                        
        while lines_to_go > 0 and self.last_read_pos != 0:
            # read the last block we haven't yet read                                                                                     
            self.file.seek(self.next_read_pos, 0)
            read_size = self.last_read_pos - self.next_read_pos
            blocks.append(self.file.read(read_size).decode('utf-8'))
            lines_found = blocks[-1].count(u'\n')
            lines_to_go -= lines_found
            self.last_read_pos = self.next_read_pos
            self.next_read_pos = 0 if self.last_read_pos - self.BLOCK_SIZE < 0 else self.last_read_pos - self.BLOCK_SIZE

        all_read_text = ''.join(reversed(blocks))

        #Now that we have found the appropriate number of lines, seek to the prior newline                                                
        #since we might have the tail end of the first of our lines, do this if we havent hit the start                                   
        if self.last_read_pos != 0:
            self.file.seek(self.next_read_pos, 0)
            read_size = self.last_read_pos - self.next_read_pos
            block = self.file.read(read_size).decode('utf-8')
            prev_newline_ptr = block.rfind(u'\n')
            all_read_text = block[prev_newline_ptr + 1:] + all_read_text

            self.last_read_pos -= prev_newline_ptr
            self.next_read_pos = 0 if self.last_read_pos - self.BLOCK_SIZE < 0 else self.last_read_pos - self.BLOCK_SIZE

        return all_read_text.splitlines()
    
    def run(self):
        self.file.seek(0, 2)
        self.next_read_pos = self.file.tell() - self.BLOCK_SIZE if self.file.tell() > self.BLOCK_SIZE else 0
        self.last_read_pos = self.file.tell()
        self.total_lines_remaining = self.numlines

        lines = self.tail()
        if self.filtered_request == False:
            self.result = lines[-self.total_lines_remaining:]
            self.total_lines_remaining = 0
            return

        while self.total_lines_remaining > 0 and len(lines) > 0:
            flist = list(filter(self.compiled_query.match, lines))
            num_filtered_interest =  self.total_lines_remaining if len(flist) > self.total_lines_remaining else len(flist)
            self.total_lines_remaining -= num_filtered_interest
            flist = flist[-num_filtered_interest:]
            flist.extend(self.result)
            self.result = flist
            lines = self.tail()
            
            
    class Logger(Resource):
    @app.route("/logfiles")
    # View a log file                                                                                                                     
    # Query params:                                                                                                                       
    # filename=name.log                                                                                                                   
    # numlines=100                                                                                                                        
    def search_logfile():
        try:
            req = LogRequest(request)
        except ValueError as e:
            abort(400, str(e))
        except TypeError:
            abort(400, 'numlines must be an integer')
        except FileNotFoundError as e:
            abort(400, str(e))
        except re.error:
            abort(400, "Invalid regular expression")
        req.run()
        return jsonify(req.result)


if __name__ == "__main__":
    app.run(debug=True)
