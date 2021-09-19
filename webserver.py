from flask import Flask,render_template, jsonify, request, abort
from flask_restful import Resource

app = Flask(__name__)

    
#REST API endpoints


class LogRequest():
    def __init__(self, request):
        self.parse(request)

    def parse(self, request):
        if request.args.get('filename'):
            self.filename = request.args.get('filename')
        else:
            raise ValueError('Filename must be specified')
        self.query = request.args.get('query')
        if request.args.get('numlines'):
            self.numlines = int(request.args.get('numlines'))
            if self.numlines < 1:
                raise ValueError('numlines must be a positive integer')
        else:
            self.numlines = 20
        self.file = open("/var/log/" + self.filename, "rb")

    def tail(self):
        total_lines_wanted = self.numlines
        
        BLOCK_SIZE = 1024
        self.file.seek(0, 2)
        block_end_byte = self.file.tell()
        lines_to_go = total_lines_wanted + 1
        block_number = -1
        blocks = [] # blocks of size BLOCK_SIZE, in reverse order starting
        # from the end of the file
        while lines_to_go > 0 and block_end_byte > 0:
            if (block_end_byte - BLOCK_SIZE > 0):
                # read the last block we haven't yet read
                self.file.seek(block_number*BLOCK_SIZE, 2)
                blocks.append(self.file.read(BLOCK_SIZE).decode('utf-8'))
            else:
                # file too small, start from begining
                self.file.seek(0,0)
                # only read what was not read
                blocks.append(self.file.read(block_end_byte).decode('utf-8'))
            lines_found = blocks[-1].count(u'\n')
            lines_to_go -= lines_found
            block_end_byte -= BLOCK_SIZE
            block_number -= 1
        all_read_text = ''.join(reversed(blocks))
        return u'\n'.join(all_read_text.splitlines()[-total_lines_wanted:])
        
        

class Logger(Resource):
                         
    @app.route("/logfiles")
    #View a log file
    #Query params:
    #  filename=name.log
    #  numlines=100
    def search_logfile():
        try:
            req = LogRequest(request)
        except ValueError as e:
            abort(400, str(e))
        except TypeError:
            abort(400, 'numlines must be an integer')
        except FileNotFoundError as e:
            abort(400, str(e))
            
            
        return jsonify(req.tail().splitlines())
            

if __name__ == "__main__":
    app.run(debug=True)
