from io import BytesIO
from flask import Blueprint, jsonify, request, send_file
from moviepy import *
from pytubefix import YouTube, innertube
from pytubefix.cli import on_progress
from pathlib import Path
from urllib.error import HTTPError
import ffmpeg, unicodedata, os, tempfile, requests

main = Blueprint('__main__', __name__, url_prefix='')

@main.route("/api/retrieve_yt_info/", methods=['GET', 'POST'])
def index():
    link = request.args.get('url')
    if not link:
        return jsonify({"error": "URL parameter is missing"}), 400

    cache_dir = tempfile.gettempdir() + "/yt_cache"
    os.makedirs(cache_dir, exist_ok=True)

    innertube._cache_dir = cache_dir
    innertube._token_file = os.path.join(cache_dir, "tokens.json")

    try:
        yt_resource = YouTube(
            link,
            client="WEB",
            use_po_token=True,
            token_file="./token_file.json",
        )

        artist = (yt_resource.author).replace('- Topic', '').strip()
        filters = [artist, '(', ')', 'Official', 'Lyrics', 'Lyric', 'Video', 'Audio', 'MV']
        title = filter_resource(yt_resource.title, filters)

        # retrieving cover
        cover = yt_resource.thumbnail_url

        # additional metadata
        song_url = "https://api.deezer.com/search"
        song_params = {
            "q": f'artist:"{artist}" track:"{title}"'
        }

        response = requests.get(song_url, params=song_params)
        formatted_meta_data = {}

        if response.status_code == 200:
            result = response.json() 

            if not result.get('data'):
                formatted_meta_data['title'] = title
                formatted_meta_data['artist'] = artist
            else:
                album_url = f"https://api.deezer.com/album/{result['data'][0].get('album').get('id')}"
                print(album_url)
                album_response = requests.get(album_url).json()

                track_list_url = f"https://api.deezer.com/album/{result['data'][0].get('album').get('id')}/tracks"
                track_list_response = requests.get(track_list_url).json()
                track_no = findTrack(track_list_response['data'], result['data'][0].get('title'), album_response.get('nb_tracks'))

                formatted_meta_data = {
                    'id': result['data'][0].get('id'),
                    'title': result['data'][0].get('title'),
                    'artist': result['data'][0].get('artist').get('name'),
                    'cover': result['data'][0].get('album').get('cover_medium'),
                    'cover_element': cover,
                    'album': result['data'][0].get('album').get('title') if title != result['data'][0].get('album').get('title') else "Single",
                    'genres': album_response.get('genres')['data'],
                    'track_no': track_no,
                    'release_date': album_response.get('release_date')
                }

            return jsonify(formatted_meta_data)

        else:
            print(f"Error: {response.status_code}")
        
    except HTTPError as http_err:
        return jsonify({
            "error": "YouTube rate limit exceeded",
            "message": str(http_err)
        }), 429

    except Exception as e:
        return jsonify({"error": "Unable to retrieve YouTube metadata", "traceback": str(e)}), 500

@main.route("/api/download_mp3/", methods=['POST'])
def download_mp3():
    resource_data = request.get_json()
    mp3_data = resource_data.get('data')

    if not mp3_data:
        return jsonify({'error', 'No data provided'}, 400)

    yt_resource = YouTube(mp3_data['url'], on_progress_callback=on_progress)
    stream = yt_resource.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()

    # Get the direct stream URL
    stream_url = stream.url

    base_dir = Path(__file__).resolve().parent

    # Build the path to ffmpeg.exe relative to this script
    ffmpeg_path = base_dir / '.' / 'ffmpeg' / 'bin' / 'ffmpeg.exe'
    ffmpeg_path = ffmpeg_path.resolve()  # Convert to absolute path


    # Stream the audio data into ffmpeg
    process = (
        ffmpeg
        .input(stream_url)
        .output('pipe:', format='mp3', acodec='libmp3lame')
        .run(capture_stdout=True, capture_stderr=True, cmd=str(ffmpeg_path))
    )
    
    buffer = BytesIO(process[0])
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=True,
        mimetype='audio/mpeg',
        download_name=f"{mp3_data['title']}"
    )

def findTrack(track_list, title, nb_tracks):
    for track in track_list:
        if track['title'] == title:
            return f"{track['track_position']} of {nb_tracks}"
        
    return None


def is_english(c):
    return c.isalpha() and unicodedata.name(c).startswith(('LATIN', 'COMMON'))

def filter_resource(title, filters):
    base = title
    for keyword in filters:
        base = base.replace(keyword, "")

    output = ""
    for s in base:
        if s == " " or s == "." or s == "," or s == "?" or s == "!":
            output += s
        else:
            filtered = filter(is_english, str(s))
            english_str = ''.join(filtered)
            output += english_str

    return output.strip()