"""
Modul untuk pemantauan penggunaan sumber daya aplikasi
"""
import os
import time
import psutil
import datetime
import threading
import json
from flask import Blueprint, jsonify, render_template, request, current_app

# Inisialisasi Blueprint untuk monitoring
monitoring_bp = Blueprint('monitoring', __name__)

# Variabel untuk menyimpan histori penggunaan RAM
memory_history = []
cpu_history = []
MAX_HISTORY_SIZE = 100  # Jumlah maksimum titik data yang disimpan

# Fungsi untuk mendapatkan informasi sumber daya
def get_resource_info():
    """
    Mendapatkan informasi tentang penggunaan sumber daya
    """
    # Dapatkan proses saat ini
    pid = os.getpid()
    process = psutil.Process(pid)
    
    # Penggunaan memori oleh proses Flask
    mem_info = process.memory_info()
    
    # Konversi ke MB
    rss_mb = mem_info.rss / 1024 / 1024
    vms_mb = mem_info.vms / 1024 / 1024
    
    # CPU usage
    cpu_percent = process.cpu_percent(interval=0.1)
    
    # Informasi penggunaan CPU keseluruhan
    overall_cpu = psutil.cpu_percent(interval=0.1)
    
    # Informasi memori sistem keseluruhan
    system_memory = psutil.virtual_memory()
    
    # Waktu aktif proses
    process_uptime = time.time() - process.create_time()
    
    # Jumlah thread
    num_threads = process.num_threads()
    
    # Jumlah open files
    try:
        open_files = len(process.open_files())
    except psutil.AccessDenied:
        open_files = -1
    
    # Jumlah koneksi aktif
    try:
        connections = len(process.connections())
    except psutil.AccessDenied:
        connections = -1
    
    # Informasi IO
    try:
        io_counters = process.io_counters()
        io_read_mb = io_counters.read_bytes / 1024 / 1024
        io_write_mb = io_counters.write_bytes / 1024 / 1024
    except psutil.AccessDenied:
        io_read_mb = -1
        io_write_mb = -1
    
    # Gunicorn worker info jika ada
    workers_info = []
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
        try:
            if 'gunicorn' in ' '.join(proc.info['cmdline'] or []):
                if proc.info['pid'] != pid:  # Tidak termasuk proses utama
                    worker_mem = proc.info['memory_info'].rss / 1024 / 1024
                    workers_info.append({
                        'pid': proc.info['pid'],
                        'memory_mb': round(worker_mem, 2),
                        'threads': proc.num_threads()
                    })
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            pass
    
    return {
        'timestamp': datetime.datetime.now().isoformat(),
        'process': {
            'pid': pid,
            'memory_rss_mb': round(rss_mb, 2),
            'memory_vms_mb': round(vms_mb, 2),
            'cpu_percent': round(cpu_percent, 2),
            'uptime_seconds': round(process_uptime, 2),
            'threads': num_threads,
            'open_files': open_files,
            'connections': connections,
            'io_read_mb': round(io_read_mb, 2) if io_read_mb != -1 else -1,
            'io_write_mb': round(io_write_mb, 2) if io_write_mb != -1 else -1
        },
        'system': {
            'total_memory_mb': round(system_memory.total / 1024 / 1024, 2),
            'available_memory_mb': round(system_memory.available / 1024 / 1024, 2),
            'used_memory_percent': system_memory.percent,
            'cpu_percent': overall_cpu
        },
        'gunicorn_workers': workers_info
    }

# Endpoint untuk mendapatkan informasi resource
@monitoring_bp.route('/resources', methods=['GET'])
def resources():
    """
    Endpoint API untuk mendapatkan informasi sumber daya
    """
    info = get_resource_info()
    
    # Simpan data untuk histori jika diminta
    if request.args.get('track', 'false').lower() == 'true':
        # Tambahkan titik data baru
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        memory_history.append({
            'time': timestamp,
            'value': info['process']['memory_rss_mb']
        })
        cpu_history.append({
            'time': timestamp,
            'value': info['process']['cpu_percent']
        })
        
        # Batasi ukuran histori
        if len(memory_history) > MAX_HISTORY_SIZE:
            memory_history.pop(0)
        if len(cpu_history) > MAX_HISTORY_SIZE:
            cpu_history.pop(0)
    
    return jsonify(info)

# Endpoint untuk mendapatkan histori penggunaan sumber daya
@monitoring_bp.route('/history', methods=['GET'])
def history():
    """
    Endpoint API untuk mendapatkan histori penggunaan sumber daya
    """
    return jsonify({
        'memory': memory_history,
        'cpu': cpu_history
    })

# Endpoint untuk memulai pelacakan otomatis
tracking_thread = None
tracking_active = False

def track_resources():
    """
    Fungsi untuk pelacakan sumber daya secara periodik
    """
    global tracking_active
    while tracking_active:
        try:
            info = get_resource_info()
            
            # Tambahkan data ke histori
            timestamp = datetime.datetime.now().strftime('%H:%M:%S')
            memory_history.append({
                'time': timestamp,
                'value': info['process']['memory_rss_mb']
            })
            cpu_history.append({
                'time': timestamp,
                'value': info['process']['cpu_percent']
            })
            
            # Batasi ukuran histori
            if len(memory_history) > MAX_HISTORY_SIZE:
                memory_history.pop(0)
            if len(cpu_history) > MAX_HISTORY_SIZE:
                cpu_history.pop(0)
                
            # Sleep selama 5 detik
            time.sleep(5)
        except Exception as e:
            print(f"Error dalam tracking thread: {str(e)}")
            time.sleep(5)

@monitoring_bp.route('/start_tracking', methods=['POST'])
def start_tracking():
    """
    Endpoint untuk memulai pelacakan otomatis penggunaan sumber daya
    """
    global tracking_thread, tracking_active
    
    if tracking_thread is None or not tracking_thread.is_alive():
        tracking_active = True
        tracking_thread = threading.Thread(target=track_resources)
        tracking_thread.daemon = True
        tracking_thread.start()
        return jsonify({'success': True, 'message': 'Tracking dimulai'})
    else:
        return jsonify({'success': False, 'message': 'Tracking sudah berjalan'})

@monitoring_bp.route('/stop_tracking', methods=['POST'])
def stop_tracking():
    """
    Endpoint untuk menghentikan pelacakan otomatis
    """
    global tracking_active
    tracking_active = False
    return jsonify({'success': True, 'message': 'Tracking dihentikan'})

# Endpoint untuk menampilkan dashboard HTML
@monitoring_bp.route('/dashboard', methods=['GET'])
def dashboard():
    """
    Endpoint untuk menampilkan dashboard monitoring
    """
    return render_template('monitoring.html') 