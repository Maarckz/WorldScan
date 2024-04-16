import signal
import socket
import ipaddress
import threading
import multiprocessing
from tqdm import tqdm
import sys


def handler(signum, frame):
    global processes
    for p in processes:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, handler)


# Defina o número máximo de threads simultâneas
MAX_THREADS = 600
thread_semaphore = threading.Semaphore(MAX_THREADS)

def scan(ip,porta, pbar):
    try:
        host = str(ip)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, porta))
        if result == 0:
            pbar.write(f"Port {porta} is open on {host}")
            with open(f'World_Port_{porta}.txt','a') as f:
                print(host, file=f)
        sock.close()
    except Exception as e:
        pbar.write(f"Error scanning {ip}: {e}")
    finally:
        # Sempre libere o semáforo, mesmo se ocorrer uma exceção
        thread_semaphore.release()
        pbar.update(1)  # Atualiza a barra de progresso

def worker(ips,porta, pbar):
    threads = []
    for ip in ips:
        thread_semaphore.acquire()  # Adquire o semáforo antes de criar uma nova thread
        t = threading.Thread(target=scan, args=(ip,porta,pbar))
        t.start()
        threads.append(t)
    
    # Aguardar todas as threads terminarem
    for t in threads:
        t.join()

ips = input('Digite a faixa de IP (Ex: xx.xx.xx.xx/xx): ')
porta = int(input('Qual porta? '))
network = ipaddress.ip_network(ips, strict=False)
ips_list = list(map(str, network.hosts()))

# Dividindo a lista de IPs em partes para cada processo
num_processes = multiprocessing.cpu_count()
chunk_size = len(ips_list) // num_processes
chunks = []
for i in range(0, len(ips_list), chunk_size):
    chunks.append(ips_list[i:i+chunk_size])

# Iniciando a barra de progresso fora do loop de chunks
total_ips = 0
for chunk in chunks:
    total_ips += len(chunk)

pbar = tqdm(total=total_ips)

# Iniciando processos para escanear em paralelo
processes = []
for chunk in chunks:
    p = multiprocessing.Process(target=worker, args=(chunk,porta, pbar))
    p.start()
    processes.append(p)

# Aguardando todos os processos terminarem
for p in processes:
    p.join()

pbar.close()
