from flask import Flask, render_template, request, redirect, url_for, session
import urllib.parse 

# STRUKTUR DATA: NODE, DOUBLY LINKED LIST, HASH TABLE

class Song:
    """Representasi data lagu."""
    def __init__(self, song_id, title, artist, genre):
        self.id = song_id
        self.title = title
        self.artist = artist
        self.genre = genre

class DLLNode:
    """Node untuk Doubly Linked List (Playlist)."""
    def __init__(self, song_id, prev_node=None, next_node=None):
        self.song_id = song_id 
        self.prev = prev_node
        self.next = next_node

class PlaylistDLL:
    """Doubly Linked List untuk menyimpan urutan lagu di playlist.
    Memungkinkan navigasi maju/mundur (next/prev) dengan mudah."""
    def __init__(self):
        self.head = None
        self.tail = None
        self.size = 0
        
    def contains_song_id(self, song_id):
        """Memeriksa apakah ID lagu sudah ada di playlist. O(N)."""
        current = self.head
        while current:
            if current.song_id == song_id:
                return True
            current = current.next
        return False

    def add_song_id(self, song_id):
        """Menambahkan ID lagu ke akhir playlist HANYA JIKA belum ada. O(N)."""
        # Perubahan: Cek duplikasi sebelum penambahan
        if self.contains_song_id(song_id):
            return False # Lagu sudah ada, batalkan penambahan
            
        new_node = DLLNode(song_id)
        if not self.head:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        self.size += 1
        return True # Penambahan berhasil

    def get_song_ids(self):
        """Mengembalikan list ID lagu dalam urutan playlist.""" 
        ids = []
        current = self.head
        while current:
            ids.append(current.song_id)
            current = current.next
        return ids

    def get_node_by_song_id(self, song_id):
        """Mengambil node pertama yang sesuai dengan song_id. O(N)."""
        current = self.head
        while current:
            if current.song_id == song_id:
                return current
            current = current.next
        return None

    def remove_all_occurrences(self, song_id):
        """Hapus semua node yang berisi song_id dari playlist."""
        current = self.head
        removed_count = 0
        while current:
            nxt = current.next  
            if current.song_id == song_id:
                if current.prev:
                    current.prev.next = current.next
                else:
                    self.head = current.next
                if current.next:
                    current.next.prev = current.prev
                else:
                    self.tail = current.prev
                removed_count += 1
                self.size -= 1
            current = nxt
        return removed_count

class LibraryHashTable:
    """Hash Table (Python Dict) untuk menyimpan semua lagu global."""
    def __init__(self):
        self.data = {}
        self.next_id = 1

    def add_song(self, title, artist, genre):
        """Menambahkan lagu baru ke library."""
        song_id = str(self.next_id)
        song = Song(song_id, title, artist, genre)
        self.data[song_id] = song
        self.next_id += 1
        return song_id

    def get_all_songs(self):
        """Mengembalikan semua objek lagu."""
        results = list(self.data.values())
        results.sort(key=lambda s: int(s.id)) 
        return results

    def get_song_by_id(self, song_id):
        """Mengambil objek lagu berdasarkan ID. O(1)."""
        return self.data.get(song_id)

    def update_song(self, song_id, title, artist, genre):
        """Update atribut lagu."""
        song = self.data.get(song_id)
        if not song:
            return False
        song.title = title
        song.artist = artist
        song.genre = genre
        return True

    def delete_song(self, song_id):
        """Hapus lagu dari library."""
        if song_id in self.data:
            del self.data[song_id]
            return True
        return False

    def search_songs(self, query):
        """Mencari lagu berdasarkan query (title, artist, id, genre). O(N)."""
        if not query:
            results = self.get_all_songs()
            return results
        
        query = query.lower()
        results = []
        for song in self.data.values():
            if (query in song.title.lower() or 
                query in song.artist.lower() or 
                query in song.genre.lower() or
                query == song.id):
                results.append(song)
        results.sort(key=lambda s: int(s.id))
        return results


# LOGIC KESAMAAN
def find_similar_song_id(current_song_id, played_song_ids):
    """
    Mencari lagu paling mirip (berdasarkan artis/genre) yang belum dimainkan.
    """
    current_song = global_library.get_song_by_id(current_song_id)
    if not current_song:
        return None

    all_songs = global_library.get_all_songs()
    played_set = set(played_song_ids)
    
    unplayed_songs = [s for s in all_songs if s.id not in played_set]

    if not unplayed_songs:
        unplayed_songs = all_songs
        unplayed_songs = [s for s in unplayed_songs if s.id != current_song_id]
        
        if not unplayed_songs:
             return None

    best_match_id = None
    max_score = -1
    
    # Skoring
    for song in unplayed_songs:
        
        score = 0
        
        # Kesamaan Genre (Skor Tinggi)
        if song.genre.lower() == current_song.genre.lower():
            score += 3
        
        # Kesamaan Artis (Skor Sedang)
        if song.artist.lower() == current_song.artist.lower():
            score += 2
        
        # Jika skor lebih tinggi, update
        if score > max_score:
            max_score = score
            best_match_id = song.id
        # Jika skornya sama, gunakan ID yang lebih kecil sebagai tie-breaker
        elif score == max_score and best_match_id and int(song.id) < int(best_match_id):
            best_match_id = song.id
        # Inisialisasi awal jika max_score adalah -1
        elif max_score == -1:
            max_score = score
            best_match_id = song.id
            
    # Fallback: Jika tidak ada lagu yang skornya > 0, ambil lagu pertama yang belum dimainkan (berdasarkan ID terendah)
    if max_score <= 0 and unplayed_songs:
        unplayed_songs.sort(key=lambda s: int(s.id))
        return unplayed_songs[0].id

    return best_match_id


# FLASK APLIKASI DAN INITIALISASI DATA
app = Flask(__name__)
app.secret_key = 'super_secret_key_musik' 

global_library = LibraryHashTable()

# Memuat data lagu awal (Total 13 lagu untuk simulasi penuh)
# ID 1 - 5 (Lagu Utama)
global_library.add_song("Hymn for the Weekend", "Coldplay", "Pop") 
global_library.add_song("Bohemian Rhapsody", "Queen", "Rock")      
global_library.add_song("Happier Than Ever", "Billie Eilish", "Pop") 
global_library.add_song("Toxic", "Britney Spears", "Pop")          
global_library.add_song("Lose Yourself", "Eminem", "Hip Hop")     

# ID 6 - 10: Lagu untuk simulasi Playlist 'sad' (ID ini digunakan di if __name__ == '__main__':)
global_library.add_song("Lovesick Girls", "BLACKPINK", "K-Pop") 
global_library.add_song("Levitating", "Dua Lipa", "Pop") 
global_library.add_song("Yellow", "Coldplay", "Rock") 
global_library.add_song("Satu-Satu", "Idgitaf", "Pop") 
global_library.add_song("Industry Baby", "Lil Nas X", "Hip Hop") 

# ID 11 - 13: Lagu untuk simulasi Similarity Test
global_library.add_song("Dynamite", "BTS", "K-Pop") # Mirip dengan ID 6
global_library.add_song("Stairway to Heaven", "Led Zeppelin", "Rock") # Mirip dengan ID 2
global_library.add_song("Monokrom", "Tulus", "Jazz") # Genre Pop Lain/Random 


# Data User: 
USERS = {
    'user1': {
        'password': 'user123',
        'playlists': {
            'favorit': PlaylistDLL(),
            'mood': PlaylistDLL(),
            'sad': PlaylistDLL() 
        },
        'active_playlist_name': None,
        'current_song_id': None,
        'current_node': None, 
        'current_queue_ids': [],    
        'current_queue_index': -1,
        'explicit_queue_ids': [], 
    },
    'admin': {
        'password': 'admin123',
        'playlists': {},
        'active_playlist_name': None,
        'current_song_id': None,
        'current_node': None, 
        'current_queue_ids': [],    
        'current_queue_index': -1,
        'explicit_queue_ids': [],
    }
}

# Fungsi pembantu untuk mengambil data user
def get_user_data(username):
    return USERS.get(username)


# USER AUTHENTICATION & ADMIN ROUTES (ASUMSIKAN SAMA)
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = USERS.get(username)

        if user and user['password'] == password:
            session['username'] = username
            if username == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            return render_template('login.html', error='Username atau password salah.')
    
    return render_template('login.html', error=None)

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
    
    songs = global_library.get_all_songs()
    return render_template('admin_dashboard.html', username=session['username'], songs=songs)

@app.route('/admin/add_song', methods=['POST'])
def admin_add_song():
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
        
    title = request.form['title']
    artist = request.form.get('artist', '')
    genre = request.form.get('genre', '')
    
    global_library.add_song(title, artist, genre)
    
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit_song/<song_id>', methods=['GET', 'POST'])
def admin_edit_song(song_id):
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
        
    song = global_library.get_song_by_id(song_id)
    if not song:
        return redirect(url_for('admin_dashboard')) # Lagu tidak ditemukan

    if request.method == 'POST':
        title = request.form['title']
        artist = request.form.get('artist', '')
        genre = request.form.get('genre', '')
        
        global_library.update_song(song_id, title, artist, genre)
        return redirect(url_for('admin_dashboard'))
    
    return render_template('admin_edit_song.html', song=song)

@app.route('/admin/delete_song/<song_id>', methods=['POST'])
def admin_delete_song(song_id):
    if 'username' not in session or session['username'] != 'admin':
        return redirect(url_for('login'))
        
    # Hapus dari library global
    if not global_library.delete_song(song_id):
        return redirect(url_for('admin_dashboard')) # lagu tidak ditemukan
        
    # Hapus dari semua playlist pengguna
    for user_data in USERS.values():
        for playlist_dll in user_data['playlists'].values():
            playlist_dll.remove_all_occurrences(song_id)
            
    # Jika lagu yang sedang diputar adalah lagu yang dihapus, hentikan pemutaran
    for user_data in USERS.values():
        if user_data['current_song_id'] == song_id:
            user_data['current_song_id'] = None
            user_data['current_node'] = None
            user_data['active_playlist_name'] = None
            user_data['current_queue_ids'] = []
            user_data['current_queue_index'] = -1
            user_data['explicit_queue_ids'] = []

    return redirect(url_for('admin_dashboard'))


# USER DASHBOARD & PLAYBACK LOGIC
@app.route('/user')
def user_dashboard():
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user_data(username)
    view_mode = request.args.get('view', 'library')
    playlist_name = request.args.get('playlist')
    search_query = request.args.get('query', '')
    
    playlists = list(user['playlists'].keys())
    
    songs = []
    current_view_playlist = None
    
    if view_mode == 'library':
        songs = global_library.search_songs(search_query)
        # Jika ada query pencarian, tampilkan query di dashboard
        if search_query:
            current_view_playlist = f"Hasil Pencarian: '{search_query}'"
    
    elif view_mode == 'playlist' and playlist_name in user['playlists']:
        playlist_dll = user['playlists'][playlist_name]
        song_ids = playlist_dll.get_song_ids()
        # Filter lagu yang masih ada di library
        songs = [global_library.get_song_by_id(sid) for sid in song_ids if global_library.get_song_by_id(sid)]
        current_view_playlist = playlist_name
        
    else:
        # Fallback
        view_mode = 'library'
        songs = global_library.get_all_songs()
        
    current_song = global_library.get_song_by_id(user['current_song_id'])
    
    # NEW: Ambil lagu di antrian eksplisit untuk ditampilkan
    explicit_queue_list = [global_library.get_song_by_id(sid) for sid in user['explicit_queue_ids'] if global_library.get_song_by_id(sid)]

    return render_template('user_dashboard.html', 
                           username=username,
                           view_mode=view_mode,
                           playlists=playlists,
                           songs=songs,
                           current_song=current_song,
                           active_playlist_name=user['active_playlist_name'],
                           current_view_playlist=current_view_playlist,
                           explicit_queue_list=explicit_queue_list) # <<< Passing data antrian


# PLAYLIST ACTIONS
@app.route('/action/create_playlist', methods=['POST'])
def action_create_playlist():
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user_data(username)
    
    new_name = request.form['new_playlist_name'].strip()
    
    if new_name and new_name not in user['playlists']:
        user['playlists'][new_name] = PlaylistDLL()
        
    return redirect(url_for('user_dashboard'))

@app.route('/action/add_to_playlist/<song_id>', methods=['POST'])
def action_add_to_playlist(song_id):
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user_data(username)
    playlist_name = request.form.get('playlist_name')
    
    # Fungsi add_song_id sekarang memiliki logic untuk mencegah duplikasi
    if playlist_name and playlist_name in user['playlists'] and global_library.get_song_by_id(song_id):
        user['playlists'][playlist_name].add_song_id(song_id)
        
    return redirect(request.referrer or url_for('user_dashboard'))

@app.route('/action/remove_from_playlist/<playlist_name>/<song_id>', methods=['POST'])
def action_remove_from_playlist(playlist_name, song_id):
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user_data(username)
    
    if playlist_name in user['playlists']:
        user['playlists'][playlist_name].remove_all_occurrences(song_id)
        
        # Jika lagu yang sedang diputar adalah bagian dari playlist ini dan dihapus
        if user['active_playlist_name'] == playlist_name and user['current_song_id'] == song_id:
            # Cari node berikutnya setelah penghapusan untuk melanjutkan
            next_node = user['playlists'][playlist_name].head
            if next_node:
                user['current_node'] = next_node
                user['current_song_id'] = next_node.song_id
            else:
                user['current_song_id'] = None
                user['current_node'] = None
                user['active_playlist_name'] = None
                
    # Redirect kembali ke view playlist yang sedang dibuka
    encoded_name = urllib.parse.quote(playlist_name)
    return redirect(url_for('user_dashboard', view='playlist', playlist=encoded_name))


@app.route('/action/set_active_playlist/<playlist_name>', methods=['POST'])
def action_set_active_playlist(playlist_name):
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user_data(username)
    
    if playlist_name in user['playlists']:
        playlist_dll = user['playlists'][playlist_name]
        
        if playlist_dll.head:
            # Mulai dari lagu pertama di playlist
            user['active_playlist_name'] = playlist_name
            user['current_node'] = playlist_dll.head
            user['current_song_id'] = playlist_dll.head.song_id
            # Reset Antrian Linear dan Eksplisit
            user['current_queue_ids'] = []
            user['current_queue_index'] = -1
            user['explicit_queue_ids'] = [] # <<< Reset Antrian Eksplisit
        
    # Redirect kembali ke view playlist yang sedang dibuka
    encoded_name = urllib.parse.quote(playlist_name)
    return redirect(url_for('user_dashboard', view='playlist', playlist=encoded_name))


@app.route('/action/delete_playlist/<playlist_name>', methods=['POST'])
def action_delete_playlist(playlist_name):
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user_data(username)
    
    if playlist_name in user['playlists']:
        # Hentikan pemutaran jika playlist yang dihapus sedang aktif
        if user['active_playlist_name'] == playlist_name:
            user['current_song_id'] = None
            user['current_node'] = None
            user['active_playlist_name'] = None
            
        del user['playlists'][playlist_name]
        
    return redirect(url_for('user_dashboard'))


# NEW FEATURE: EXPLICIT QUEUE
@app.route('/action/add_to_explicit_queue/<song_id>', methods=['POST'])
def action_add_to_explicit_queue(song_id):
    """Menambahkan lagu ke antrian eksplisit (diputar selanjutnya)."""
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user_data(username)
    
    if global_library.get_song_by_id(song_id):
        # Tambahkan ID lagu ke antrian eksplisit (selalu di akhir)
        user['explicit_queue_ids'].append(song_id)
        
        # Jika tidak ada lagu yang sedang diputar, langsung putar lagu ini
        if not user['current_song_id']:
             user['current_song_id'] = user['explicit_queue_ids'].pop(0)
             # Pastikan semua mode lain dinonaktifkan
             user['active_playlist_name'] = None 
             user['current_node'] = None 
             user['current_queue_ids'] = [] 
             user['current_queue_index'] = -1
             
    return redirect(request.referrer or url_for('user_dashboard'))


# PLAYBACK CONTROLS (PLAY, NEXT, PREV, STOP)
@app.route('/action/play_from_library/<song_id>', methods=['POST'])
def action_play_from_library(song_id):
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user_data(username)
    
    # 1. Tentukan antrian linear berdasarkan hasil pencarian (atau seluruh library)
    search_query = request.args.get('query', '')
    queue_songs = global_library.search_songs(search_query)
    queue_ids = [s.id for s in queue_songs]
    
    if queue_ids:
        try:
            # 2. Cari index lagu yang diputar dalam antrian
            index = queue_ids.index(song_id)
            
            # 3. Set status user
            user['active_playlist_name'] = None 
            user['current_node'] = None
            user['current_queue_ids'] = queue_ids 
            user['current_queue_index'] = index 
            user['current_song_id'] = song_id 
            user['explicit_queue_ids'] = [] # <<< Reset antrian eksplisit
            
        except ValueError:
            return redirect(request.referrer or url_for('user_dashboard'))
    
    return redirect(request.referrer or url_for('user_dashboard'))

@app.route('/action/play_from_playlist/<playlist_name>/<song_id>', methods=['POST'])
def action_play_from_playlist(playlist_name, song_id):
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user_data(username)
    
    if playlist_name in user['playlists']:
        playlist_dll = user['playlists'][playlist_name]
        start_node = playlist_dll.get_node_by_song_id(song_id)
        
        if start_node:
            # Set status user ke mode Playlist/DLL
            user['active_playlist_name'] = playlist_name
            user['current_node'] = start_node 
            user['current_song_id'] = song_id 
            user['current_queue_ids'] = [] 
            user['current_queue_index'] = -1
            user['explicit_queue_ids'] = [] # <<< Reset antrian eksplisit
            
    return redirect(request.referrer or url_for('user_dashboard'))

@app.route('/action/stop', methods=['POST'])
def action_stop():
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    username = session['username']
    user = get_user_data(username)
    # Reset semua status player
    user['current_song_id'] = None
    user['current_node'] = None
    user['active_playlist_name'] = None
    user['current_queue_ids'] = []
    user['current_queue_index'] = -1
    user['explicit_queue_ids'] = [] # <<< Hapus juga antrian eksplisit
    return redirect(request.referrer or url_for('user_dashboard'))

@app.route('/action/next_prev/<action>', methods=['POST'])
def action_next_prev(action):
    if 'username' not in session or session['username'] == 'admin':
        return redirect(url_for('login'))
    
    username = session['username']
    user = get_user_data(username)
    
    new_song_id = None
    
    if action == 'next':
        
        # Prioritas 1: Antrian Eksplisit (NEW FEATURE) 
        if user.get('explicit_queue_ids') and user['explicit_queue_ids']:
            new_song_id = user['explicit_queue_ids'].pop(0) # Ambil lagu pertama (FIFO)
            
            # Reset semua state lain karena ini adalah lagu yang diprioritaskan
            user['current_node'] = None 
            user['active_playlist_name'] = None 
            user['current_queue_ids'] = [] 
            user['current_queue_index'] = -1
            
        # Prioritas 2: Navigasi di dalam Antrian Linear/Similarity (Queue dari Library/Search) 
        elif user['current_queue_ids'] and user['current_queue_index'] < len(user['current_queue_ids']) - 1:
            user['current_queue_index'] += 1
            new_song_id = user['current_queue_ids'][user['current_queue_index']]
        
        # Prioritas 3: Lanjutkan di DLL Playlist
        elif user['current_node'] and user['active_playlist_name']: 
            if user['current_node'].next: 
                user['current_node'] = user['current_node'].next
                new_song_id = user['current_node'].song_id
            else:
                # DLL berakhir, reset ke state default, lagu berikutnya adalah dari similarity
                user['active_playlist_name'] = None 
                user['current_node'] = None
                user['current_queue_ids'] = []
                user['current_queue_index'] = -1
                
        # Prioritas 4: Rekomendasi Similarity (Jika lagu yang sedang dimainkan ada)
        elif user['current_song_id']:
            # Lanjut ke lagu yang paling mirip dan belum dimainkan
            new_song_id = find_similar_song_id(user['current_song_id'], user['current_queue_ids'])
            
            # Tambahkan lagu similarity ke current_queue_ids untuk melacak histori
            if new_song_id:
                user['current_queue_ids'].append(new_song_id)
                user['current_queue_index'] = len(user['current_queue_ids']) - 1
            
    elif action == 'prev':
        
        # Prioritas 1: Navigasi di dalam Antrian Linear/Similarity
        if user['current_queue_ids'] and user['current_queue_index'] > 0:
            user['current_queue_index'] -= 1
            new_song_id = user['current_queue_ids'][user['current_queue_index']]
        
        # Prioritas 2: Kembali ke lagu sebelumnya di DLL Playlist
        elif user['current_node'] and user['active_playlist_name']:
            if user['current_node'].prev:
                user['current_node'] = user['current_node'].prev
                new_song_id = user['current_node'].song_id
            elif user['current_node']:
                # Sudah di awal DLL, putar ulang lagu yang sama
                new_song_id = user['current_node'].song_id
        
        # Prioritas 3: Navigasi Awal Queue Linear (tanpa DLL)
        elif user['current_queue_ids'] and user['current_queue_index'] == 0:
             # Tidak bisa mundur lagi, tetap di lagu yang sama
             new_song_id = user['current_queue_ids'][0]

                
    # SET NEW SONG ID and FALLBACK STOP 
    if new_song_id:
        user['current_song_id'] = new_song_id
    else:
        # Stop jika tidak ada navigasi yang berhasil atau semua antrian/playlist habis
        user['current_song_id'] = None 
        user['current_node'] = None
        user['current_queue_ids'] = []
        user['current_queue_index'] = -1
        user['explicit_queue_ids'] = [] # Reset juga antrian eksplisit

    return redirect(request.referrer or url_for('user_dashboard'))


if __name__ == '__main__':
    # Memuat lagu ke playlist dummy untuk testing
    user1_playlists = USERS['user1']['playlists']
    # Lagu ID '1' akan ditambahkan sekali saja ke playlist 'mood'
    user1_playlists['favorit'].add_song_id('1') 
    user1_playlists['favorit'].add_song_id('3') 
    user1_playlists['favorit'].add_song_id('5')
    user1_playlists['mood'].add_song_id('2') 
    user1_playlists['mood'].add_song_id('4')
    user1_playlists['mood'].add_song_id('1') 
    # Inisialisasi playlist sad (ID 6, 7, 8, 9, 10)
    user1_playlists['sad'].add_song_id('6')
    user1_playlists['sad'].add_song_id('7')
    user1_playlists['sad'].add_song_id('8')
    user1_playlists['sad'].add_song_id('9')
    user1_playlists['sad'].add_song_id('10')
    
    # Menambahkan user/password dummy jika belum ada
    if 'user1' not in USERS:
        USERS['user1'] = {
            'password': 'user123',
            'playlists': user1_playlists,
            'active_playlist_name': None,
            'current_song_id': None,
            'current_node': None, 
            'current_queue_ids': [],    
            'current_queue_index': -1,
            'explicit_queue_ids': []
        }
        
        
    if 'admin' not in USERS:
         USERS['admin'] = {
            'password': 'admin123',
            'playlists': {},
            'active_playlist_name': None,
            'current_song_id': None,
            'current_node': None, 
            'current_queue_ids': [],    
            'current_queue_index': -1,
            'explicit_queue_ids': []
        }

    app.run(debug=True)