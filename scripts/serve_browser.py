"""Open the standalone browser demo locally using only Python's standard library."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import sys
import webbrowser

sys.path.insert(0,str(Path(__file__).resolve().parent))
from build_pages import build, ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port',type=int,default=8040)
    parser.add_argument('--no-open',action='store_true')
    args=parser.parse_args()
    directory=build(ROOT/'dist/browser-local',base='/')
    class Handler(SimpleHTTPRequestHandler):
        extensions_map={**SimpleHTTPRequestHandler.extensions_map,'.mjs':'text/javascript','.js':'text/javascript'}
        def log_message(self,*args):pass
    server=ThreadingHTTPServer(('127.0.0.1',args.port),partial(Handler,directory=str(directory)))
    url=f'http://127.0.0.1:{server.server_port}/'
    print(f'KONAET browser demo: {url}\nKeep this window open. Ctrl+C stops the demo.',flush=True)
    if not args.no_open:webbrowser.open(url)
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()


if __name__=='__main__':main()
