import threading
import time

import uvicorn
import webview


def start_server() -> None:
	"""
	Creates the uvicorn server and runs it
	:return:
	"""
	config = uvicorn.Config("backend.main:app", host="127.0.0.1", port=8000, log_level="info")
	server = uvicorn.Server(config)
	server.run()


def main():
	server_thread = threading.Thread(target=start_server, daemon=True)
	server_thread.start()
	# Give the server a moment to start
	time.sleep(0.8)
	webview.create_window("Schedule", "http://127.0.0.1:8000")
	webview.start()


if __name__ == "__main__":
	main() 